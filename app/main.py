import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import FileResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.limiter import limiter

from app import models  # noqa: F401
from app.api.routes import router, verify_router
from app.db import Base, engine


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="Bulk Certificate Generator", lifespan=lifespan)


app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.include_router(router)
app.include_router(verify_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


INDEX_PATH = os.path.join(os.path.dirname(__file__), "static", "index.html")


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(INDEX_PATH, media_type="text/html")
