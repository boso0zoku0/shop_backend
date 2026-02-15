from datetime import datetime, timedelta
from json import JSONEncoder

import jwt
from core.config import settings
import bcrypt


def convert_to_iso_string(data):
    if isinstance(data, dict):
        return {k: convert_to_iso_string(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [convert_to_iso_string(item) for item in data]
    elif isinstance(data, datetime):
        return data.isoformat()
    else:
        return data


class JWTHelper:

    def encode_jwt(
        self,
        payload: dict,
        expire_minutes_access: int = settings.auth_jwt.access_token_expire_minutes,
        expire_minutes_refresh: int = settings.auth_jwt.refresh_token_expire_days,
        private_key: str = settings.auth_jwt.private_key_path.read_text(),
        algorithm: str = settings.auth_jwt.algorithm,
        is_refresh: bool = False,
    ):

        now = datetime.now()
        to_copy = payload.copy()
        if is_refresh:
            expire = now + timedelta(minutes=expire_minutes_refresh)
        else:
            expire = now + timedelta(minutes=expire_minutes_access)

        converted_payload = convert_to_iso_string(to_copy | {"iat": now, "exp": expire})
        return jwt.encode(
            payload=converted_payload, key=private_key, algorithm=algorithm
        )

    def decode_jwt(
        self,
        token: str,
        public_key: str = settings.auth_jwt.public_key_path.read_text(),
        algorithm: str = settings.auth_jwt.algorithm,
    ):
        return jwt.decode(token=token, key=public_key, algorithms=[algorithm])

    def hash_password(self, password: str) -> bytes:
        pwd_encode = password.encode("utf-8")
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(pwd_encode, salt)

    def validate_password(self, password: str, hashed_password: bytes) -> bool:
        return bcrypt.checkpw(
            password=password.encode("utf-8"), hashed_password=hashed_password
        )


helper = JWTHelper()
