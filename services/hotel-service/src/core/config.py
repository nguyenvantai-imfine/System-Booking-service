from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Cấu hình ứng dụng
    APP_NAME: str = "Hotel Service"
    API_V1_STR: str = "/api/v1"

    # Cấu hình CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            v = v.strip()
            if v.startswith("[") and v.endswith("]"):
                import json
                try:
                    return json.loads(v)
                except Exception:
                    pass
            return [i.strip() for i in v.split(",") if i.strip()]
        return v
    
    # Cấu hình Database SQL Server
    DB_SERVER: str = "localhost"         # Tên Server hoặc IP (ví dụ: localhost, localhost\\SQLEXPRESS)
    DB_PORT: int = 1433                  # Cổng mặc định của SQL Server là 1433
    DB_NAME: str = "hotel_service"    # Tên Database của bạn
    DB_USER: str = "sa"                  # Tài khoản SQL Server
    DB_PASSWORD: str = "12345678" # Mật khẩu SQL Server
    DB_DRIVER: str = "ODBC Driver 18 for SQL Server" # Driver ODBC đã cài trên máy
    DB_TRUSTED_CONNECTION: bool = False  # Bật True nếu dùng Windows Authentication (SQLEXPRESS)

    # Cấu hình JWT Auth (đồng bộ với user-service)
    JWT_SECRET_KEY: str = "booking_super_secret_jwt_key_2026_xyz!@#"
    JWT_ALGORITHM: str = "HS256"

    @property
    def DATABASE_URL(self) -> str:
        # Chuỗi kết nối SQLAlchemy cho SQL Server qua pyodbc
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