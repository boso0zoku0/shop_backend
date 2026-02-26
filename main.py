import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, status, Request
from starlette.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.staticfiles import StaticFiles

from core.redis.manager import redis_manager
from core.views import router as games_router
from core.super_user import super_user_games_router

from core.auth.views import router as auth_router
from core.config import settings
from core.frontend_db.views import router
from core.users.views import router as users_router
from core.websockets.endpoints import router as ws_router
from core.faststream.handlers import broker
from core.payments.views import router as payment_router
from core.payments.webhooks import router as payment_webhooks_router
from core.media.views import router as media_router


@asynccontextmanager
async def lifespan(app):
    await broker.start()
    await redis_manager.initialize()
    yield
    await broker.stop()
    await redis_manager.close()


app = FastAPI(lifespan=lifespan)

app.include_router(games_router)
app.include_router(users_router)
app.include_router(super_user_games_router)
app.include_router(payment_router)
app.include_router(payment_webhooks_router)
app.include_router(media_router)
app.include_router(auth_router)

app.include_router(router)

app.include_router(ws_router)

logging.basicConfig(
    format=settings.logging.log_format,
    level=settings.logging.log_level_name,
    datefmt=settings.logging.date_format,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],  # Разрешаем все методы
    allow_headers=["*"],  # Разрешаем все заголовки
)
app.mount("/static", StaticFiles(directory="static"), name="static")


class UnicornException(Exception):
    def __init__(self, name: str):
        self.name = name


@app.exception_handler(UnicornException)
async def unicorn_exception_handler(request: Request, exc: UnicornException):
    return JSONResponse(
        status_code=418,
        content={"message": f"Oops! {exc.name} did something. There goes a rainbow..."},
    )


@app.middleware("http")
async def catch_shop_paths(request: Request, call_next):
    if request.url.path.startswith("/qwe"):
        return JSONResponse(
            status_code=404,
            content={"detail": f"Path not found: {request.url.path}"},
        )

    # Иначе продолжаем нормальную обработку
    response = await call_next(request)
    return response


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
