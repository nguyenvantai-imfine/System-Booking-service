from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings

class GatewaySettings(BaseSettings):
    APP_NAME: str = "API Gateway"
    PORT: int = 8080

    # Backend Microservices
    HOTEL_SERVICE_URL: str = "http://127.0.0.1:8000"
    USER_SERVICE_URL: str = "http://127.0.0.1:8001"
    ROOM_SERVICE_URL: str = "http://127.0.0.1:8002"
    BOOKING_SERVICE_URL: str = "http://127.0.0.1:8003"
    PAYMENT_SERVICE_URL: str = "http://127.0.0.1:8004"
    NOTIFICATION_SERVICE_URL: str = "http://127.0.0.1:8005"

    # CORS Configuration
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

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

settings = GatewaySettings()
