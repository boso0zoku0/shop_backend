from datetime import datetime
from typing import Literal

from fastapi import Form
from pydantic import BaseModel

from core.schemas.privilege_level import PrivilegeLevel


class UsersBase(BaseModel):
    id: int
    username: str
    password: str
    date_registration: datetime

    class Config:
        arbitrary_types_allowed = True


class UsersGet(BaseModel):
    username: str
    date_registration: datetime


class UserInfo(BaseModel):
    username: str
    date_registration: datetime
    privilege: PrivilegeLevel | None
    cookie_privileged: datetime | None
    cookie_privileged_expires: datetime | None
    game: str | None
