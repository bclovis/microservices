"""
Pokemon Drafter - Backend Red Team
Main application entry point with layered architecture
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# Core imports
from core.config import settings
from core.logging import setup_logging

# Repository imports
from repositories.database import init_db

# Route imports
from api.routes import auth_routes, team_routes, game_routes, pokemon_routes


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events"""
    # Startup
    setup_logging()
    init_db()  # Initialize database tables
    yield
    # Shutdown
    # Add cleanup code here if needed


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_routes.router)
app.include_router(team_routes.router)
app.include_router(game_routes.router)
app.include_router(pokemon_routes.router)


# Root endpoints
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": f"Pokemon Drafter - {settings.team_color} Team Backend",
        "team": settings.team_color,
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "team": settings.team_color
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
