import os
import urllib.parse
from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # App
    APP_NAME: str = "Notification Service"
    PORT: int = 8005
    API_V1_STR: str = "/api/v1"
    JWT_SECRET_KEY: str = "booking_super_secret_jwt_key_2026_xyz!@#"
    JWT_ALGORITHM: str = "HS256"
    INTERNAL_SERVICE_SECRET: str = ""
    TRUSTED_INTERNAL_CIDRS: str = (
        "127.0.0.1/32,::1/128,172.16.0.0/12"
    )

    # Database
    DB_SERVER: str = "localhost\\SQLEXPRESS"
    DB_PORT: int = 0
    DB_NAME: str = "notification_service"
    DB_USER: str = "sa"
    DB_PASSWORD: str = "Password123!"
    DB_DRIVER: str = "ODBC Driver 18 for SQL Server"
    DB_TRUSTED_CONNECTION: bool = True

    # RabbitMQ
    RABBITMQ_HOST: str = "localhost"
    RABBITMQ_PORT: int = 5672
    RABBITMQ_USER: str = "guest"
    RABBITMQ_PASSWORD: str = "guest"
    RABBITMQ_ENABLED: bool = True

    # SMTP Settings
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_TLS: bool = True
    SMTP_FROM_EMAIL: str = "no-reply@hotelbooking.com"
    SMTP_FROM_NAME: str = "Hệ Thống Đặt Phòng Khách Sạn"
    MOCK_EMAIL_SEND: bool = Field(
        default=True,
        validation_alias=AliasChoices("EMAIL_MOCK", "MOCK_EMAIL_SEND"),
    )

    @property
    def DATABASE_URL(self) -> str:
        server_str = self.DB_SERVER
        if self.DB_PORT and self.DB_PORT != 0 and "\\" not in self.DB_SERVER:
            server_str = f"{self.DB_SERVER}:{self.DB_PORT}"

        if self.DB_TRUSTED_CONNECTION:
            return (
                f"mssql+pyodbc://@{server_str}/{self.DB_NAME}"
                f"?driver={self.DB_DRIVER.replace(' ', '+')}"
                f"&trusted_connection=yes"
                f"&TrustServerCertificate=yes"
            )

        encoded_password = urllib.parse.quote_plus(self.DB_PASSWORD)
        return (
            f"mssql+pyodbc://{self.DB_USER}:{encoded_password}"
            f"@{server_str}/{self.DB_NAME}"
            f"?driver={self.DB_DRIVER.replace(' ', '+')}"
            f"&TrustServerCertificate=yes"
        )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

settings = Settings()
