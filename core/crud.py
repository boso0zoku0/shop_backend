import enum
from datetime import datetime, timezone
from typing import Sequence, Literal
from urllib.parse import urlencode

from certifi import where
from fastapi import Depends, HTTPException, status, Request
from fastapi import Query
from sqlalchemy import (
    select,
    asc,
    and_,
    func,
    desc,
    Integer,
    insert,
    update,
    cast,
    Date,
    union_all,
    text,
)
from sqlalchemy.exc import NoResultFound, IntegrityError

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import outerjoin
from starlette.responses import RedirectResponse

from core import db_helper
from core.auth.crud import get_user_by_cookie
from core.models import (
    Games,
    GamesUserLiked,
    Users,
    GamesUserRatings,
)
from core.schemas import GamesBase
from core.schemas.privilege_level import PrivilegeLevel


class SortDate(enum.Enum):
    DATE = "date"
    YEAR = "year"


class GameRating(enum.Enum):
    ONE = 1
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5


async def check_games(
    session: AsyncSession = Depends(db_helper.session_dependency()),
    future: bool = False,
):
    if not future:
        stmt = select(Games).order_by(asc(Games.id))
        res = await session.execute(stmt)
        games = res.scalars().all()
        return games
    else:
        pass


async def check_game(
    game: str, session: AsyncSession = Depends(db_helper.session_dependency())
) -> Games | None:
    try:
        stmt = select(Games).where(Games.name == game)
        res = await session.execute(stmt)
        games = res.scalars().one()
        return games
    except NoResultFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Game not found"
        )


async def games_catalog(
    session: AsyncSession = Depends(db_helper.session_dependency()),
):
    extracted_year = func.cast(func.split_part(Games.release_year, ",", 2), Integer)

    # Создание подзапроса с группировкой по жанрам и сортировкой по году
    subquery = (
        select(
            Games,
            func.row_number()
            .over(partition_by=Games.genre, order_by=desc(extracted_year))
            .label("row_num"),
        ).select_from(
            Games
        )  # После .subquery() объект становится производной таблицей
        # select_from(subquery) явно указывает, что выбираем из этой таблицы
        .subquery()
    )

    # Основной запрос с фильтрацией по номеру строки
    stmt = (
        select(Games)
        .join(subquery, Games.id == subquery.c.id)
        .where(subquery.c.row_num <= 2)
    )

    result = await session.execute(stmt)
    games = result.scalars().unique().all()
    return games


# группировка по жанрам и сортировка по годам
async def game_catalor(session: AsyncSession = Depends(db_helper.session_dependency())):

    subquery = select()


async def game_select_genre(
    genre: Literal["ACTION", "ADVENTURE", "RPG", "STRATEGY", "SIMULATION"],
    session: AsyncSession = Depends(db_helper.session_dependency()),
):
    stmt = select(Games).where(Games.genre == genre)
    res = await session.execute(stmt)
    games = res.scalars().all()
    return games


async def create_favorite_game(
    game: str,
    request: Request,
    session: AsyncSession = Depends(db_helper.session_dependency()),
):
    user = await get_user_by_cookie(session, request)

    # if not user:
    #     raise HTTPException(
    #         status_code=status.HTTP_404_NOT_FOUND,
    #         detail="Please register on the site to add games to your favorites.",
    #     )

    stmt = select(Games.name, Games.genre).where(Games.name == game)
    result = await session.execute(stmt)
    game, genre = result.first()
    if not game:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Game not found"
        )

    stmt = select(Users.favorite_genre).where(Users.username == user.username)
    res = await session.execute(stmt)
    users_favorite_genre = res.scalar()

    stmt = select(GamesUserLiked.id).where(
        and_(GamesUserLiked.user_id == user.id, GamesUserLiked.game == game)
    )
    res = await session.execute(stmt)
    users = res.first()

    if users:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have already added the game to your favorites.",
        )
    else:
        stmt = GamesUserLiked(
            game=game,
            user_id=user.id,
        )
        session.add(stmt)
        await session.commit()

        users_favorite_genre[genre.value] += 1  # Учту какого жанра игру лайкнул юзер
        stmt_2 = (
            update(Users)
            .where(Users.username == user.username)
            .values(favorite_genre=users_favorite_genre)
        )
        await session.execute(stmt_2)
        await session.commit()
        return {"Game added successfully"}


async def sort_date(
    decreasing: bool = Query(True),
    sort_by: Literal["date", "year", "ranking_popularity"] = Query("date"),
    session: AsyncSession = Depends(db_helper.session_dependency),
):
    if sort_by == "date":
        order_field = Games.release_year
    elif sort_by == "year":
        extracted_year = func.cast(
            func.split_part(Games.release_year, ", ", 2), Integer
        )
        order_field = extracted_year

    elif sort_by == "ranking_popularity":
        likes_subquery = (
            select(
                GamesUserLiked.game, func.count(GamesUserLiked.game).label("like_count")
            )
            .group_by(GamesUserLiked.game)
            .subquery()
        )
        # JOIN по полю name (Games.name = likes_subquery.game)
        stmt = (
            select(Games, likes_subquery.c.like_count)
            .join(
                likes_subquery, Games.name == likes_subquery.c.game
            )  # ← JOIN по name!
            .order_by(
                desc(likes_subquery.c.like_count)
                if decreasing
                else asc(likes_subquery.c.like_count)
            )
        )
        result = await session.execute(stmt)
        rows = result.all()
        return [
            {
                "id": game_obj.id,
                "name": game_obj.name,
                "genre": (
                    game_obj.genre.value
                    if hasattr(game_obj.genre, "value")
                    else str(game_obj.genre)
                ),
                "release_year": game_obj.release_year,
                "story": game_obj.story,
                "gameplay": game_obj.gameplay,
                "graphics": game_obj.graphics,
                "game_development": game_obj.game_development,
                "gallery": game_obj.gallery,
                "like_count": like_count or 0,
                "is_popular": (like_count or 0) > 5,
            }
            for game_obj, like_count in rows
        ]

    else:
        extracted_year = func.cast(
            func.split_part(Games.release_year, ", ", 2), Integer
        )
        order_field = extracted_year

    if decreasing and not sort_by == "ranking_popularity":
        stmt = select(Games).order_by(desc(order_field))
    else:
        stmt = select(Games).order_by(asc(order_field))

    result = await session.execute(stmt)
    games = result.scalars().all()

    return games


async def add_rating_for_game(
    game: str,
    rating: int,
    request: Request,
    session: AsyncSession = Depends(db_helper.session_dependency),
):
    try:
        user = await get_user_by_cookie(session, request)

        stmt_game_rating = insert(GamesUserRatings).values(
            user_id=user.id,
            game=game,
            rating=rating,
        )
        await session.execute(stmt_game_rating)
        await session.commit()
        return {f"You rated it {rating} for game {game}" "Thanks for your opinion"}

    except IntegrityError as e:
        if "duplicate key" in str(e):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"You've already added {game} to your favorites.",
            )


async def get_rating_for_games(
    session: AsyncSession = Depends(db_helper.session_dependency),
):
    stmt_sub = (
        select(
            GamesUserRatings.game,
            func.sum(GamesUserRatings.rating).label("total_ratings"),
            func.count(GamesUserRatings.rating).label("rating_count"),
        )
        .group_by(GamesUserRatings.game)  # ← group_by НА select!
        .subquery()
    )

    stmt = select(
        stmt_sub.c.game,
        (stmt_sub.c.total_ratings / stmt_sub.c.rating_count).label("average_rating"),
    ).order_by(desc(stmt_sub.c.total_ratings))
    result = await session.execute(stmt)
    data = result.all()

    return [
        {
            "game": game,
            "average_rating": float(average_rating) if average_rating else None,
        }
        for game, average_rating in data
    ]


async def hidden_games(
    request: Request,
    selected_games: bool = True,
    session: AsyncSession = Depends(db_helper.session_dependency),
):
    try:
        cookie = request.cookies.get("session_id")

        subquery = (
            select(GamesUserLiked.game)
            .join(Users, GamesUserLiked.user_id == Users.id)
            .where(Users.cookie == cookie)
            .subquery()  # ← подзапрос
        )
        if selected_games:
            stmt = select(Games).where(Games.name.not_in(select(subquery.c.game)))
            res = await session.execute(stmt)
            data_t = res.scalars().all()
            return data_t
        else:
            stmt = select(Games).where(Games.name.in_(select(subquery.c.game)))
            res = await session.execute(stmt)
            data_t = res.scalars().all()
            return data_t

    except IntegrityError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Log in to your account to use this feature.",
        )


# изменил логику на гибридные свойства модели
# async def distribution_future(
#     session: AsyncSession = Depends(db_helper.session_dependency),
# ):
#     now = datetime.now(tz=timezone.utc)
#
#     # сбросить флаг у тех игр дата выхода которых уже наступила
#
#     stmt = (
#         update(Games)
#         .where(
#             and_(cast(Games.release_year, Date) < now.date()), Games.is_future == True
#         )
#         .values(is_future=False)
#     )
#     await session.execute(stmt)
#     await session.commit()
#
#     select_stmt = select(Games).where(Games.is_future == True)
#     result = await session.execute(select_stmt)
#     future_games = result.scalars().all()
#
#     # 3. Возвращаем список. Если игр нет, вернется [], и FastAPI будет доволен
#     return future_games


async def distribution_future(
    session: AsyncSession = Depends(db_helper.session_dependency),
):

    select_stmt = select(Games).where(Games.is_future == True)
    result = await session.execute(select_stmt)
    future_games = result.scalars().all()
    return future_games


async def get_liked_games(
    request: Request,
    session: AsyncSession = Depends(db_helper.session_dependency),
):
    user = await get_user_by_cookie(session, request)

    stmt = (
        select(
            GamesUserLiked.user_id,
            func.coalesce(func.array_agg(GamesUserLiked.game), []).label("games"),
        )
        .join(Users, GamesUserLiked.user_id == Users.id)
        .where(Users.id == user.id)
        .group_by(GamesUserLiked.user_id)
    )
    res = await session.execute(stmt)
    liked_games = res.first()
    if liked_games is None:
        return ["Empty"]
    return {"id": liked_games.user_id, "games": liked_games.games}


# async def user_interactions(
#     request: Request,
#     session: AsyncSession = Depends(db_helper.session_dependency),
# ):
#     user = await get_user_by_cookie(request=request, session=session)
#     stmt = (
#         select(
#             Users.username,
#             Users.date_registration,
#             Users.is_superuser,
#             GamesUserLiked.game,
#             GamesUserLiked.created_at,
#             GamesUserRatings.game,
#             GamesUserRatings.rating,
#             GamesUserRatings.created_at,
#         )
#         .outerjoin(GamesUserRatings, Users.id == GamesUserRatings.user_id)
#         .outerjoin(GamesUserLiked, Users.id == GamesUserLiked.user_id)
#         .where(Users.id == user.id)
#     )


async def user_interactions(
    request: Request,
    session: AsyncSession = Depends(db_helper.session_dependency),
):
    user = await get_user_by_cookie(request=request, session=session)

    subquery_ratings = (
        select(
            GamesUserRatings.user_id,
            func.array_agg(
                func.json_build_object(
                    "game",
                    GamesUserRatings.game,
                    "rating",
                    GamesUserRatings.rating,
                    "created_at",
                    GamesUserRatings.created_at,
                )
            ).label("rating_games"),
        )
        .where(GamesUserRatings.user_id == user.id)
        .group_by(GamesUserRatings.user_id)
        .subquery()
    )

    subquery_liked = (
        select(
            GamesUserLiked.user_id,
            func.array_agg(
                func.json_build_object(
                    "game",
                    GamesUserLiked.game,
                    "created_at",
                    GamesUserLiked.created_at,
                ),
            ).label("liked_games"),
        )
        .where(GamesUserLiked.user_id == user.id)
        .group_by(GamesUserLiked.user_id)
        .subquery()
    )

    stmt = (
        select(
            Users.username,
            Users.date_registration,
            Users.is_superuser,
            func.coalesce(subquery_ratings.c.rating_games, []).label("rating_games"),
            func.coalesce(subquery_liked.c.liked_games, []).label("liked_games"),
        )
        .outerjoin(subquery_ratings, Users.id == subquery_ratings.c.user_id)
        .outerjoin(subquery_liked, Users.id == subquery_liked.c.user_id)
        .where(Users.id == user.id)
    )
    res = await session.execute(stmt)
    data = res.first()

    return {
        "username": data.username,
        "date_registration": data.date_registration,
        "is_superuser": data.is_superuser,
        "rating_games": data.rating_games or [],
        "liked_games": data.liked_games or [],
    }


async def get_games_preferred(
    request: Request,
    session: AsyncSession = Depends(db_helper.session_dependency),
):
    user = await get_user_by_cookie(session, request)
    stmt = select(Users.favorite_genre).where(Users.id == user.id)
    res = await session.execute(stmt)
    genres = res.scalar()
    all_games = await genres_preference_algorithm(
        session=session,
        action=genres["action"],
        rpg=genres["rpg"],
        strategy=genres["strategy"],
    )
    return all_games


async def genres_preference_algorithm(
    action: int,
    rpg: int,
    strategy: int,
    session: AsyncSession = Depends(db_helper.session_dependency),
):
    if (action + rpg + strategy) <= 3:
        params = {"decreasing": "true", "sort_by": "date"}
        query_string = urlencode(params)  # "decreasing=True&sort_by=date"
        return RedirectResponse(
            url=f"/games/sort/by-date?{query_string}",
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
        )
    stmt_action = (
        select(Games)
        .where(Games.genre == "ACTION")
        .order_by(func.random())
        .limit(action)
    )
    stmt_rpg = (
        select(Games).where(Games.genre == "RPG").order_by(func.random()).limit(rpg)
    )
    stmt_strategy = (
        select(Games)
        .where(Games.genre == "STRATEGY")
        .order_by(func.random())
        .limit(strategy)
    )

    combined_stmt = union_all(stmt_action, stmt_rpg, stmt_strategy)
    res = await session.execute(combined_stmt)
    all_games = res.fetchall()
    # games = [dict(row._mapping) for row in all_games.mappings().all()]
    return [
        GamesBase(
            name=game.name,
            genre=game.genre.value,
            release_year=game.release_year,
            story=game.story,
            gameplay=game.gameplay,
            graphics=game.graphics,
            game_development=game.game_development,
            gallery=game.gallery,
        )
        for game in all_games
    ]


async def create_privilege_level(
    privilege: PrivilegeLevel,
    request: Request,
    session: AsyncSession = Depends(db_helper.session_dependency),
):
    user = await get_user_by_cookie(session, request)
    expire_cookie: int = 0
    if privilege.value == "weak":
        expire_cookie = 20
    if privilege.value == "medium":
        expire_cookie = 2000
    if privilege.value == "best":
        expire_cookie = 10000
    await session.execute(
        update(Users)
        .where(Users.username == user.username)
        .values(
            privilege=privilege,
            cookie_privileged=func.now(),
            cookie_privileged_expires=text(
                f"TIMEZONE('utc', now()) + interval '{expire_cookie} minutes'"
            ),
        )
    )
    await session.commit()
