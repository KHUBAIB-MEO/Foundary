from fastapi import FastAPI, HTTPException
from app.database.connection import create_db_and_tables, get_async_session
from app.database.models.product import Product
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_db_and_tables()
    yield

app = FastAPI(lifespan=lifespan)