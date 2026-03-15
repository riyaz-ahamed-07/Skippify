"""
Skippify Backend — FastAPI Application Entry Point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from database import init_db
from routers import admin, student, attendance


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup."""
    await init_db()
    yield


app = FastAPI(
    title="Skippify API",
    description="Engineering student attendance tracker and skip planner",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(admin.router)
app.include_router(student.router)
app.include_router(attendance.router)


@app.get("/")
async def root():
    return {"app": "Skippify", "status": "running"}
