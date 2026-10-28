# -*- coding: utf-8 -*-
import sys
import os
from datetime import datetime, timedelta
from decimal import Decimal
import unittest

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
PAYMENT_SERVICE_DIR = os.path.join(PROJECT_ROOT, "services", "payment-service")

if PAYMENT_SERVICE_DIR not in sys.path:
    sys.path.insert(0, PAYMENT_SERVICE_DIR)

os.chdir(PAYMENT_SERVICE_DIR)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from src.models.thanh_toan import Base, ThanhToanModel, TrangThaiThanhToanEnum, PhuongThucThanhToanEnum
from src.services.payment_service import PaymentService

class TestPaymentStatsP34(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            echo=False,
        )
        Base.metadata.create_all(cls.engine)
        cls.SessionLocal = sessionmaker(bind=cls.engine)

    def setUp(self):
        self.db = self.SessionLocal()
        self.db.query(ThanhToanModel).delete()
        self.db.commit()

    def tearDown(self):
        self.db.close()

    def test_payment_stats_today_and_total_revenue(self):
        print("\n======================================================================")
        print("KIỂM TRA TÍNH TOÁN DOANH THU THỰC TẾ TRONG PAYMENT SERVICE (P3.4)")
        print("======================================================================")

        now = datetime.utcnow()
        yesterday = now - timedelta(days=1)

        # 1. Giao dịch thành công hôm nay: 2.000.000 đ
        tx_today_1 = ThanhToanModel(
            id_dat_phong=101,
            ma_booking="BK-TEST-001",
            so_tien=Decimal("2000000.00"),
            phuong_thuc=PhuongThucThanhToanEnum.VNPAY.value,
            trang_thai=TrangThaiThanhToanEnum.SUCCESS.value,
            ma_giao_dich_gateway="TX-TODAY-001",
            ngay_tao=now,
        )

        # 2. Giao dịch thành công hôm nay: 1.500.000 đ
        tx_today_2 = ThanhToanModel(
            id_dat_phong=102,
            ma_booking="BK-TEST-002",
            so_tien=Decimal("1500000.00"),
            phuong_thuc=PhuongThucThanhToanEnum.MOMO.value,
            trang_thai=TrangThaiThanhToanEnum.SUCCESS.value,
            ma_giao_dich_gateway="TX-TODAY-002",
            ngay_tao=now,
        )

        # 3. Giao dịch PENDING hôm nay: 500.000 đ (không được cộng vào doanh thu)
        tx_today_pending = ThanhToanModel(
            id_dat_phong=103,
            ma_booking="BK-TEST-003",
            so_tien=Decimal("500000.00"),
            phuong_thuc=PhuongThucThanhToanEnum.CREDIT_CARD.value,
            trang_thai=TrangThaiThanhToanEnum.PENDING.value,
            ma_giao_dich_gateway="TX-TODAY-003",
            ngay_tao=now,
        )

        # 4. Giao dịch thành công hôm qua: 3.000.000 đ (chỉ cộng vào total_revenue, không cộng vào today_revenue)
        tx_yesterday = ThanhToanModel(
            id_dat_phong=104,
            ma_booking="BK-TEST-004",
            so_tien=Decimal("3000000.00"),
            phuong_thuc=PhuongThucThanhToanEnum.CASH.value,
            trang_thai=TrangThaiThanhToanEnum.SUCCESS.value,
            ma_giao_dich_gateway="TX-YESTERDAY-004",
            ngay_tao=yesterday,
        )

        self.db.add_all([tx_today_1, tx_today_2, tx_today_pending, tx_yesterday])
        self.db.commit()

        stats = PaymentService.get_stats(self.db)
        print(f" -> Tổng doanh thu (total_revenue): {stats.total_revenue:,.0f} đ (Kỳ vọng: 6,500,000 đ)")
        print(f" -> Doanh thu hôm nay (today_revenue): {stats.today_revenue:,.0f} đ (Kỳ vọng: 3,500,000 đ)")
        print(f" -> Tổng giao dịch: {stats.total_transactions} (Thành công: {stats.success_count}, Chờ: {stats.pending_count})")

        self.assertEqual(stats.total_revenue, 6500000.0)
        self.assertEqual(stats.today_revenue, 3500000.0)
        self.assertEqual(stats.total_transactions, 4)
        self.assertEqual(stats.success_count, 3)
        self.assertEqual(stats.pending_count, 1)
        print(" -> [PASS] Doanh thu hôm nay và tổng doanh thu được tính toán hoàn toàn chính xác!")

    def test_api_stats_endpoint(self):
        print("\n======================================================================")
        print("KIỂM TRA ENDPOINT GET /api/v1/payments/stats VỚI QUYỀN ADMIN")
        print("======================================================================")
        import jwt
        from fastapi.testclient import TestClient
        from src.main import app
        from src.core.config import settings
        from src.core.database import get_db
        def override_get_db():
            db = self.SessionLocal()
            try:
                yield db
            finally:
                db.close()

        app.dependency_overrides[get_db] = override_get_db

        client = TestClient(app)
        admin_token = jwt.encode(
            {"sub": "1", "role": "ADMIN", "type": "access"},
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM,
        )
        headers = {"Authorization": f"Bearer {admin_token}"}

        # Seed data
        now = datetime.utcnow()
        tx = ThanhToanModel(
            id_dat_phong=201,
            ma_booking="BK-API-001",
            so_tien=Decimal("5000000.00"),
            phuong_thuc=PhuongThucThanhToanEnum.VNPAY.value,
            trang_thai=TrangThaiThanhToanEnum.SUCCESS.value,
            ma_giao_dich_gateway="TX-API-001",
            ngay_tao=now,
        )
        self.db.add(tx)
        self.db.commit()

        resp = client.get("/api/v1/payments/stats", headers=headers)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        print(f" -> Response payload: {data}")
        self.assertIn("today_revenue", data)
        self.assertEqual(data["today_revenue"], 5000000.0)
        self.assertEqual(data["total_revenue"], 5000000.0)
        print(" -> [PASS] API /stats trả về today_revenue chuẩn xác!")

        app.dependency_overrides.clear()

if __name__ == "__main__":
    unittest.main()
