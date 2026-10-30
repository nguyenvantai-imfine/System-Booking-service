
import json
from typing import Annotated, List, Union
from urllib.parse import quote_plus

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):

    # Cau hinh ung dung
    APP_NAME: str = "Booking Service"
    PORT: int = 8003
    API_V1_STR: str = "/api/v1"

    # Cau hinh CORS
    CORS_ORIGINS: Annotated[List[str], NoDecode] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(
        cls,
        value: Union[str, List[str]],
    ) -> List[str]:

        if isinstance(value, str):
            value = value.strip()

            if not value:
                return []

            if value.startswith("[") and value.endswith("]"):
                try:
                    parsed = json.loads(value)

                    if isinstance(parsed, list):
                        return [
                            str(item).strip().rstrip("/")
                            for item in parsed
                            if str(item).strip()
                        ]

                except (json.JSONDecodeError, TypeError):
                    pass

            return [
                item.strip().strip('"').strip("'").rstrip("/")
                for item in value.split(",")
                if item.strip()
            ]

        if isinstance(value, list):
            return [
                str(item).strip().rstrip("/")
                for item in value
                if str(item).strip()
            ]

        raise ValueError("CORS_ORIGINS phai la danh sach cac origin.")

    # Cau hinh SQL Server
    DB_SERVER: str = "localhost"
    DB_PORT: int = 1433
    DB_NAME: str = "booking_service"
    DB_USER: str = "sa"
    DB_PASSWORD: str = "12345678"
    DB_DRIVER: str = "ODBC Driver 18 for SQL Server"

    # True: Windows Authentication
    # False: SQL Server Authentication
    DB_TRUSTED_CONNECTION: bool = True

    # Cau hinh JWT
    # Khi ket noi User Service, phai dung secret va algorithm tuong thich.
    JWT_SECRET_KEY: str = "change_this_secret_key"
    JWT_ALGORITHM: str = "HS256"

    # Thoi gian giu cho
    HOLD_MINUTES: int = 15

    # RabbitMQ
    RABBITMQ_HOST: str = "localhost"
    RABBITMQ_PORT: int = 5672
    RABBITMQ_USER: str = "guest"
    RABBITMQ_PASSWORD: str = "guest"

    # Cac service lien quan
    PAYMENT_SERVICE_URL: str = "http://127.0.0.1:8004/api/v1"
    ROOM_SERVICE_URL: str = "http://127.0.0.1:8002/api/v1"
    NOTIFICATION_SERVICE_URL: str = "http://127.0.0.1:8005/api/v1"

    # Secret xac thuc service noi bo
    INTERNAL_SERVICE_SECRET: str = ""

    @property
    def DATABASE_URL(self) -> str:
        """
        Tao connection string cho SQL Server.
        Ho tro Windows Authentication va SQL Server Authentication.
        """

        server = self.DB_SERVER.strip()

        if not server:
            raise ValueError("DB_SERVER khong duoc de trong.")

        if not self.DB_NAME.strip():
            raise ValueError("DB_NAME khong duoc de trong.")

        if not self.DB_DRIVER.strip():
            raise ValueError("DB_DRIVER khong duoc de trong.")

        # Neu DB_SERVER co ten instance, vi du localhost\\SQLEXPRESS,
        # khong ghep them port vao server.
        has_instance = "\\" in server

        if not has_instance and self.DB_PORT > 0:
            server = f"{server},{self.DB_PORT}"

        driver = quote_plus(self.DB_DRIVER.strip())

        if self.DB_TRUSTED_CONNECTION:
            return (
                f"mssql+pyodbc://@{server}/{self.DB_NAME}"
                f"?driver={driver}"
                f"&trusted_connection=yes"
                f"&TrustServerCertificate=yes"
            )

        username = quote_plus(self.DB_USER)
        password = quote_plus(self.DB_PASSWORD)

        return (
            f"mssql+pyodbc://{username}:{password}"
            f"@{server}/{self.DB_NAME}"
            f"?driver={driver}"
            f"&TrustServerCertificate=yes"
        )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
