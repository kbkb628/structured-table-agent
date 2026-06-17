from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.analysis import router as analysis_router
from app.api.demo import router as demo_router
from app.api.eval import router as eval_router
from app.api.files import router as files_router
from app.core.config import UPLOAD_DIR
from app.storage.database import init_db


@asynccontextmanager
async def lifespan(_: FastAPI):
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    init_db()
    yield


app = FastAPI(title="Structured Table Analysis MVP", lifespan=lifespan)


app.include_router(demo_router)
app.include_router(files_router)
app.include_router(analysis_router)
app.include_router(eval_router)
