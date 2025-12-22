from fastapi import FastAPI
from contextlib import asynccontextmanager
from src.api.routes import router
from src.db.session import engine
from src.db.models import Base
from src.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)
app.include_router(router)
