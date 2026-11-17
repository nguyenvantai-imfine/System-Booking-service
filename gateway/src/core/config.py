import os
from pathlib import Path
from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings


def _resolve_env_file() -> str:
    """Explicit ENV_FILE, otherwise service-local dotenv. Process env wins."""
    explicit = os.environ.get("ENV_FILE")
    if explicit:
        env_path = Path(explicit).expanduser()
        if not env_path.is_absolute():
            raise ValueError("ENV_FILE must be an absolute path.")
        return str(env_path)
    return str(Path(__file__).resolve().parents[2] / ".env")

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
        env_file = _resolve_env_file()
        env_file_encoding = "utf-8"
        extra = "ignore"

settings = GatewaySettings()
