import enum
from typing import Literal

from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Mapped

from core.models import GameGenre


class GamesBase(BaseModel):
    name: str
    genre: Literal["ACTION", "ADVENTURE", "RPG", "STRATEGY", "SIMULATION"]
    release_year: str | None = None
    story: str
    gameplay: str
    graphics: str | None = None
    game_development: str | None = None
    gallery: list[str] | None = None

    # class Config:
    #     arbitrary_types_allowed = True
    #
    @field_validator("genre", mode="before")
    def decode_enum(cls, v):
        # Если пришел объект Enum (например, GameGenre.ACTION), берем его значение
        if hasattr(v, "value"):
            v = v.value
        # Принудительно делаем заглавными, чтобы совпало с Literal["ACTION"]
        if isinstance(v, str):
            return v.upper()
        return v


class GamesGet(GamesBase):
    id: int


class GamesCharacteristicsPost(BaseModel):
    game_name: str
    oc: str
    cpu: str
    gpu: str
    ram: str
    disk_space: str
