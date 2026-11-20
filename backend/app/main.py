"""FastAPI програмын эхлэл. Ажиллуулах: uvicorn app.main:app --reload  (API баримт: /docs)."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import admin, analysis, auth, courses, health, links, postings, programs, reports, users
from app.core.config import get_settings

settings = get_settings()
app = FastAPI(title=settings.app_name, version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins, allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])

for r in (health, auth, users, programs, courses, postings, analysis, links, reports, admin):
    app.include_router(r.router)
