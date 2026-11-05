import os
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.database.base import Base
from app.database.session import engine
from app.api import (
    auth,
    dashboard,
    requisitions,
    scorecards,
    resumes,
    candidates,
    scoring,
    client_portal,
    pipeline,
    privacy,
    audit
)

# Initialize database schema
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="HireAI – Intelligent Recruitment & Candidate Shortlisting API",
    description="Enterprise recruitment automation, scorecard extraction, deterministic candidate scoring, and client portal.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(requisitions.router)
app.include_router(scorecards.router)
app.include_router(resumes.router)
app.include_router(candidates.router)
app.include_router(scoring.router)
app.include_router(client_portal.router)
app.include_router(pipeline.router)
app.include_router(privacy.router)
app.include_router(audit.router)


@app.get("/")
def root():
    return {
        "service": "HireAI Backend API",
        "tagline": "Smarter Hiring. Faster Shortlists. Fairer Decisions.",
        "status": "operational",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}

