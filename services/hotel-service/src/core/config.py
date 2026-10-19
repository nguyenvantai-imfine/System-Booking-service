from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Cấu hình ứng dụng
    APP_NAME: str = "Hotel Service"
    API_V1_STR: str = "/api/v1"
    
    # Cấu hình Database SQL Server
    DB_SERVER: str = "localhost"         # Tên Server hoặc IP (ví dụ: localhost, localhost\\SQLEXPRESS)
    DB_PORT: int = 1433                  # Cổng mặc định của SQL Server là 1433
    DB_NAME: str = "hotel_service"    # Tên Database của bạn
    DB_USER: str = "sa"                  # Tài khoản SQL Server
    DB_PASSWORD: str = "12345678" # Mật khẩu SQL Server
    DB_DRIVER: str = "ODBC Driver 18 for SQL Server" # Driver ODBC đã cài trên máy

    @property
    def DATABASE_URL(self) -> str:
        # Chuỗi kết nối SQLAlchemy cho SQL Server qua pyodbc
        return (
            f"mssql+pyodbc://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_SERVER}:{self.DB_PORT}/{self.DB_NAME}"
            f"?driver={self.DB_DRIVER.replace(' ', '+')}"
            f"&TrustServerCertificate=yes"
        )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

settings = Settings()