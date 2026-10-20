from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Cấu hình ứng dụng
    APP_NAME: str = "Room Service"
    PORT: int = 8002
    API_V1_STR: str = "/api/v1"

    # Cấu hình Database SQL Server
    DB_SERVER: str = "localhost\\SQLEXPRESS"
    DB_PORT: int = 0
    DB_NAME: str = "room_service"
    DB_USER: str = "sa"
    DB_PASSWORD: str = "12345678"
    DB_DRIVER: str = "ODBC Driver 18 for SQL Server"
    DB_TRUSTED_CONNECTION: bool = True

    # Cấu hình JWT Auth dùng chung với User & Hotel Service
    JWT_SECRET_KEY: str = "booking_super_secret_jwt_key_2026_xyz!@#"
    JWT_ALGORITHM: str = "HS256"

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

        import urllib.parse
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
