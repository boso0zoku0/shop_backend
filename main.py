import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

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


@asynccontextmanager
async def lifespan(app):
    await broker.start()
    yield
    await broker.stop()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await redis_manager.initialize()
    yield
    # Shutdown
    await redis_manager.close()


app = FastAPI(lifespan=lifespan)


app.include_router(games_router)
app.include_router(users_router)
app.include_router(super_user_games_router)
app.include_router(payment_router)
app.include_router(payment_webhooks_router)
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

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
