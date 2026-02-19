from typing import Iterable, cast

from redis import Redis

from core.config import settings
from core.schemas import GamesBase

redis = Redis(
    host=settings.redis.host,
    port=settings.redis.port,
    db=1,
    decode_responses=True,
)


class GamesCrud:
    def __init__(self, redis: Redis, name_db):
        self.redis = redis
        self.name_db = name_db

    async def save_games(self, game: GamesBase) -> None:
        await redis.hset(
            name=self.name_db,
            key=game.name,
            value=game.model_dump_json(),
        )

    async def get(self) -> list[GamesBase]:
        return [
            GamesBase.model_validate_json(value)
            for value in cast(
                Iterable[str],
                redis.hvals(
                    name=self.name_db,
                ),
            )
        ]

    async def get_by_name(self, name: str) -> GamesBase | None:
        get_data = cast(
            str | None,
            await redis.hget(name=self.name_db, key=name),
        )
        if get_data:
            return GamesBase.model_validate_json(get_data)
        return None

    async def create_game(self, game: GamesBase) -> GamesBase:
        add_film = GamesBase(**game.model_dump())
        await self.save_games(add_film)
        return add_film

    async def exists(self, name: str) -> bool:
        return cast(
            bool,
            await redis.hexists(name=self.name_db, key=name),
        )


redis_crud = GamesCrud(redis, name_db="games")
