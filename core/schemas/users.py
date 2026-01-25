from datetime import datetime

from fastapi import Form
from pydantic import BaseModel


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
