"""FastAPI main application."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.middleware.correlation_id import CorrelationIdMiddleware
from app.middleware.exception_handler import ExceptionHandlerMiddleware
from app.middleware.request_logging import RequestLoggingMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    print("Application starting...")

    # Run seed data in development
    if settings.environment == "development":
        from app.database import SessionLocal
        from app.seed import seed_data

        db = SessionLocal()
        try:
            seed_data(db)
        finally:
            db.close()

    yield

    # Shutdown
    print("Application shutting down...")


# Create FastAPI application
app = FastAPI(
    title="Ericsson GembaONE Platform",
    description="AI-assisted field data capture and auditable Excel ingestion platform",
    version="0.1.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add custom middleware (order matters - exception handler first, then correlation ID, then logging)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(CorrelationIdMiddleware)
app.add_middleware(ExceptionHandlerMiddleware)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Ericsson GembaONE Platform",
        "version": "0.1.0",
        "status": "running",
    }


# Include routers (imported at the end to avoid circular imports)
from app.routers import auth, checklist_templates, checklists, ingestions, mappings  # noqa: E402

app.include_router(auth.router, prefix="/api/v1")
app.include_router(checklist_templates.router, prefix="/api/v1")
app.include_router(checklists.router, prefix="/api/v1")
app.include_router(ingestions.router, prefix="/api/v1")
app.include_router(mappings.router, prefix="/api/v1")
