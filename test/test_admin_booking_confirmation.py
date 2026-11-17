import unittest
from unittest.mock import MagicMock,patch
from fastapi.testclient import TestClient
from test_legacy_auth_fallback import load_service_module


class AdminBookingConfirmationTests(unittest.TestCase):
    def test_customer_cannot_confirm_but_admin_and_service_can(self):
        main=load_service_module('booking-service','src.main')
        import importlib
        deps=importlib.import_module('src.api.v1.dependencies')
        endpoints=importlib.import_module('src.api.v1.endpoints.bookings')
        db=MagicMock()
        def database():yield db
        main.app.dependency_overrides[endpoints.get_db]=database
        try:
            for role,status in [('CUSTOMER',403),('PARTNER',403),('ADMIN',200),('SERVICE',200)]:
                main.app.dependency_overrides[deps.get_current_user_or_internal_service]=lambda role=role:{'sub':'17','role':role}
                with patch.object(endpoints.BookingService,'confirm_booking',return_value=None) as confirm:
                    # Skip response-model serialization; this unit tests authorization.
                    if status==200:
                        result=endpoints.confirm_booking('17',db,{'sub':'17','role':role})
                        self.assertIsNone(result);confirm.assert_called_once()
                    else:
                        response=TestClient(main.app).patch('/api/v1/bookings/17/confirm')
                        self.assertEqual(response.status_code,status);confirm.assert_not_called()
        finally:main.app.dependency_overrides.clear()


if __name__=='__main__':unittest.main()
