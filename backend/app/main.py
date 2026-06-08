from fastapi import FastAPI

from app.api.files import router as files_router
from app.core.config import UPLOAD_DIR
from app.storage.database import init_db

app = FastAPI(title="Structured Table Analysis MVP")


@app.on_event("startup")
def startup() -> None:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    init_db()


app.include_router(files_router)
