from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from nexus_ai.api.routes import router
from nexus_ai.config import get_settings
from nexus_ai.db.bootstrap import init_database
from nexus_ai.patient_finance.api_routes import finance_router
from nexus_ai.patient_finance.mongodb import close_mongodb, init_mongodb


@asynccontextmanager
async def lifespan(_: FastAPI):
    import os
    settings = get_settings()
    if settings.google_api_key and "GEMINI_API_KEY" not in os.environ:
        os.environ["GEMINI_API_KEY"] = settings.google_api_key

    init_database()
    await init_mongodb()
    try:
        yield
    finally:
        await close_mongodb()


class ApiKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        settings = get_settings()
        if not settings.app_api_key:
            return await call_next(request)
        if request.method in {"GET", "HEAD", "OPTIONS"}:
            return await call_next(request)
        if request.headers.get("x-api-key") != settings.app_api_key:
            return JSONResponse({"detail": "Invalid or missing API key."}, status_code=401)
        return await call_next(request)


settings = get_settings()
app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.add_middleware(ApiKeyMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)
app.include_router(finance_router)
