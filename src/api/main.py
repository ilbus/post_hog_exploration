from fastapi import FastAPI
from contextlib import asynccontextmanager
from src.api.routes import router
from src.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Base.metadata.create_all(bind=engine)  <-- Removed: Managed by Alembic
    yield


app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)
app.include_router(router)
