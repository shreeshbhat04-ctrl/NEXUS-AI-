from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from nexus_ai.config import get_settings
from nexus_ai_doctor.api.routes import router

settings = get_settings()

app = FastAPI(title="nexus_ai Doctor Module", description="Clinical assistant platform for doctors.")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("static/dicoms", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(router, prefix="/api/v1")
