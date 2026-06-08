from fastapi import FastAPI

from app.core.config import UPLOAD_DIR

app = FastAPI(title="Structured Table Analysis MVP")


@app.on_event("startup")
def startup() -> None:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
