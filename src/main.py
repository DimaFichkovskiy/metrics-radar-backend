import os
import logging.config
import databases
import aioredis

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_pagination import add_pagination

from src import routes
from src.config import Config
from src.database import get_db_session

db = databases.Database(Config.POSTGRES_URL)

app = FastAPI()

app.include_router(routes.auth_router)
app.include_router(routes.users_router)
app.include_router(routes.company_router)
app.include_router(routes.management_router)
app.include_router(routes.notifications_router)
app.include_router(routes.quiz_router)
app.include_router(routes.workflow_router)
app.include_router(routes.export_router)

add_pagination(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# logging.config.fileConfig("logging.ini")
# logger = logging.getLogger()


@app.on_event("startup")
async def startup():
    # logger.info("START")
    await db.connect()
    app.state.redis = await aioredis.from_url(Config.REDIS_URL)


@app.on_event("shutdown")
async def shutdown():
    await db.disconnect()
    await app.state.redis.close()


@app.get('/')
def health_check():
    return {"status": "Working"}
