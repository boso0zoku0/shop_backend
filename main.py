import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from core.views import router as games_router
from core.super_user import super_user_games_router

from core.auth.views import router as auth_router
from core.config import settings
from core.frontend_db.views import router

from core.websockets.endpoints import router as ws_router
from core.websockets.helper import broker


@asynccontextmanager
async def lifespan(app):
    await broker.start()
    yield
    await broker.stop()


app = FastAPI(lifespan=lifespan)


app.include_router(games_router)
app.include_router(super_user_games_router)

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
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],  # Разрешаем все методы
    allow_headers=["*"],  # Разрешаем все заголовки
)

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
