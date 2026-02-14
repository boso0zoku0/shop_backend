from sqlalchemy.orm import DeclarativeBase, declared_attr
import logging
from pathlib import Path

from pydantic_settings import BaseSettings
from pydantic import BaseModel
from typing import Literal
import logging

BASE_DIR = Path(__file__).parent.parent


class Base(DeclarativeBase):
    __abstract__ = True

    @declared_attr.directive
    def __tablename__(cls) -> str:
        return f"{cls.__name__.lower()}"


class LoggingConfig(BaseModel):
    log_level_name: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    log_format: str = (
        "[%(asctime)s.%(msecs)03d] %(module)10s:%(lineno)-3d %(levelname)-7s - %(message)s"
    )
    date_format: str = "%Y-%m-%d %H:%M:%S"

    @property
    def log_level(self) -> int:
        return logging.getLevelNamesMapping()[self.log_level_name]


class AuthJWT(BaseModel):
    private_key_path: Path = BASE_DIR / "core" / "auth" / "certs" / "jwt-private.pem"
    public_key_path: Path = BASE_DIR / "core" / "auth" / "certs" / "jwt-public.pem"
    algorithm: str = "RS256"
    access_token_expire_minutes: int = 10080
    refresh_token_expire_days: int = 302400


class ApiV1Prefix(BaseModel):
    prefix: str = "/v1"
    auth: str = "/auth"


class AccessToken(BaseModel):
    lifetime_seconds: int = 10080
    reset_password_token_secret: str
    verification_token_secret: str


class Setting(BaseSettings):
    api_v1_prefix: str = "/api/v1"
    db_url: str = "postgresql+asyncpg://postgres:matvei225CC@localhost:5432/shop"
    db_echo: bool = True
    # access_token: AccessToken = AccessToken()
    logging: LoggingConfig = LoggingConfig()
    auth_jwt: AuthJWT = AuthJWT()


settings = Setting()
