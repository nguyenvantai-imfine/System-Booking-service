import os
import sys
import json
import unittest
from datetime import date
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError, URLError

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
ROOM_SERVICE_DIR = os.path.join(PROJECT_ROOT, "services", "room-service")


def activate_room_service():
    for module_name in list(sys.modules):
        if module_name == "src" or module_name.startswith("src."):
            del sys.modules[module_name]
    for path in list(sys.path):
        normalized_path = os.path.normcase(os.path.abspath(path or os.getcwd()))
        if normalized_path.startswith(
            os.path.normcase(os.path.join(PROJECT_ROOT, "services"))
        ):
            sys.path.remove(path)
    sys.path.insert(0, ROOM_SERVICE_DIR)
    os.chdir(ROOM_SERVICE_DIR)


class TestRoomRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        activate_room_service()
        from src.api.v1.dependencies import check_hotel_ownership
        from src.core.config import settings
        from src.core.database import Base
        from src.core.security import decode_token
        from src.models import LoaiPhongModel, PhongModel
        from src.schemas import (
            LoaiPhongCreate,
            LoaiPhongUpdate,
            PhongCreate,
            PhongStatusUpdate,
        )
        from src.services import RoomService, RoomTypeService

        cls.check_hotel_ownership = staticmethod(check_hotel_ownership)
        cls.settings = settings
        cls.base = Base
        cls.decode_token = staticmethod(decode_token)
        cls.room_models = (LoaiPhongModel, PhongModel)
        cls.room_type_create = LoaiPhongCreate
        cls.room_type_update = LoaiPhongUpdate
        cls.room_create = PhongCreate
        cls.room_status_update = PhongStatusUpdate
        cls.room_service = RoomService
        cls.room_type_service = RoomTypeService

    def setUp(self):
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        self.base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.db = self.Session()
        self.settings.JWT_SECRET_KEY = "room-regression-jwt-secret"
        self.settings.HOTEL_SERVICE_URL = "http://hotel-service.test/api/v1"
        self.settings.BOOKING_SERVICE_URL = "http://booking-service.test/api/v1"
        self.settings.BOOKING_SERVICE_TIMEOUT = 0.1
        self.settings.INTERNAL_SERVICE_SECRET = "room-regression-internal-secret"

    def tearDown(self):
        self.db.close()
        self.engine.dispose()

    @staticmethod
    def _hotel_response(owner_id):
        response = MagicMock()
        response.__enter__.return_value = response
        response.read.return_value = ('{"id_tai_khoan": %s}' % owner_id).encode()
        return response

    def test_partner_ownership_requires_verified_hotel_owner(self):
        partner = {"sub": "42", "role": "PARTNER"}
        with patch(
            "urllib.request.urlopen",
            return_value=self._hotel_response(42),
        ) as urlopen:
            self.check_hotel_ownership(7, partner)
        self.assertIn("/hotels/7", urlopen.call_args.args[0].full_url)

        with patch(
            "urllib.request.urlopen",
            return_value=self._hotel_response(43),
        ):
            with self.assertRaises(HTTPException) as raised:
                self.check_hotel_ownership(7, partner)
        self.assertEqual(raised.exception.status_code, 403)

    def test_partner_ownership_fails_closed_for_upstream_errors_and_bad_data(self):
        partner = {"sub": "42", "role": "PARTNER"}
        failures = (
            URLError("unavailable"),
            TimeoutError("timeout"),
            HTTPError("hotel", 401, "unauthorized", None, None),
            HTTPError("hotel", 403, "forbidden", None, None),
            HTTPError("hotel", 500, "server error", None, None),
        )
        for failure in failures:
            with self.subTest(failure=type(failure).__name__):
                with patch("urllib.request.urlopen", side_effect=failure):
                    with self.assertRaises(HTTPException) as raised:
                        self.check_hotel_ownership(7, partner)
                self.assertEqual(raised.exception.status_code, 503)

        not_found = HTTPError("hotel", 404, "not found", None, None)
        with patch("urllib.request.urlopen", side_effect=not_found):
            with self.assertRaises(HTTPException) as raised:
                self.check_hotel_ownership(7, partner)
        self.assertEqual(raised.exception.status_code, 404)

        for response_body in (b"{}", b"[]", b'{"id_tai_khoan": "invalid"}', b"{"):
            response = MagicMock()
            response.__enter__.return_value = response
            response.read.return_value = response_body
            with self.subTest(response_body=response_body):
                with patch("urllib.request.urlopen", return_value=response):
                    with self.assertRaises(HTTPException) as raised:
                        self.check_hotel_ownership(7, partner)
                self.assertEqual(raised.exception.status_code, 503)

    def test_claim_mismatch_and_admin_do_not_call_hotel_service(self):
        with patch("urllib.request.urlopen") as urlopen:
            with self.assertRaises(HTTPException) as raised:
                self.check_hotel_ownership(
                    7,
                    {"sub": "42", "role": "PARTNER", "hotel_id": 8},
                )
            self.assertEqual(raised.exception.status_code, 403)

            self.check_hotel_ownership(7, {"sub": "1", "role": "ADMIN"})
        urlopen.assert_not_called()

    def test_room_type_room_crud_status_and_database_constraints(self):
        room_type = self.room_type_service.create_room_type(
            self.db,
            7,
            self.room_type_create(
                ten_loai_phong="Standard",
                gia_co_ban_mot_dem=1200000,
            ),
        )
        room = self.room_service.create_room(
            self.db,
            room_type.id_loai_phong,
            self.room_create(so_phong="101"),
        )
        self.assertEqual(room.id_khach_san, 7)
        self.assertEqual(room_type.so_luong_phong, 1)

        with self.assertRaises(HTTPException) as duplicate:
            self.room_service.create_room(
                self.db,
                room_type.id_loai_phong,
                self.room_create(so_phong="101"),
            )
        self.assertEqual(duplicate.exception.status_code, 409)

        updated_type = self.room_type_service.update_room_type(
            self.db,
            room_type.id_loai_phong,
            self.room_type_update(gia_co_ban_mot_dem=1500000),
        )
        self.assertEqual(float(updated_type.gia_co_ban_mot_dem), 1500000)

        updated_room = self.room_service.update_room_status(
            self.db,
            room.id_phong,
            self.room_status_update(trang_thai="OCCUPIED"),
        )
        self.assertEqual(updated_room.trang_thai, "OCCUPIED")
        with self.assertRaises(HTTPException) as invalid_transition:
            self.room_service.update_room_status(
                self.db,
                room.id_phong,
                self.room_status_update(trang_thai="MAINTENANCE"),
            )
        self.assertEqual(invalid_transition.exception.status_code, 400)
        self.room_service.update_room_status(
            self.db,
            room.id_phong,
            self.room_status_update(trang_thai="AVAILABLE"),
        )

        with self.assertRaises(HTTPException) as in_use_type:
            self.room_type_service.delete_room_type(
                self.db,
                room_type.id_loai_phong,
            )
        self.assertEqual(in_use_type.exception.status_code, 409)

        self.room_service.delete_room(self.db, room.id_phong)
        self.assertEqual(
            self.room_service.get_room_by_id(self.db, room.id_phong).trang_thai,
            "INACTIVE",
        )

    def test_availability_distinguishes_empty_result_from_booking_failure(self):
        room_type = self.room_type_service.create_room_type(
            self.db,
            7,
            self.room_type_create(
                ten_loai_phong="Available",
                gia_co_ban_mot_dem=900000,
            ),
        )
        room = self.room_service.create_room(
            self.db,
            room_type.id_loai_phong,
            self.room_create(so_phong="202"),
        )

        def response_with(payload):
            response = MagicMock()
            response.__enter__.return_value = response
            response.status = 200
            response.read.return_value = payload
            return response

        with patch(
            "src.services.room_service.urlopen",
            return_value=response_with(b"[]"),
        ):
            available = self.room_service.get_available_rooms(
                self.db,
                7,
                date(2026, 11, 10),
                date(2026, 11, 12),
            )
        self.assertEqual([item.id_phong for item in available], [room.id_phong])

        with patch(
            "src.services.room_service.urlopen",
            return_value=response_with(
                json.dumps([room.id_phong]).encode("utf-8")
            ),
        ):
            unavailable = self.room_service.get_available_rooms(
                self.db,
                7,
                date(2026, 11, 10),
                date(2026, 11, 12),
            )
        self.assertEqual(unavailable, [])

        with patch(
            "src.services.room_service.urlopen",
            side_effect=HTTPError("booking", 503, "unavailable", None, None),
        ):
            with self.assertRaises(HTTPException) as raised:
                self.room_service.get_available_rooms(
                    self.db,
                    7,
                    date(2026, 11, 10),
                    date(2026, 11, 12),
                )
        self.assertEqual(raised.exception.status_code, 503)

    def test_room_jwt_rejects_missing_secret(self):
        self.settings.JWT_SECRET_KEY = ""
        with self.assertRaises(HTTPException) as raised:
            self.decode_token("not-a-token")
        self.assertEqual(raised.exception.status_code, 503)
