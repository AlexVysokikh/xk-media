from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

from app.settings import settings
from app.schemas import HealthResponse
from app.db import init_db, SessionLocal
from app import models  # noqa: F401 - ensure models are imported
from app.deps_auth import RedirectException


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create tables and ensure admin exists
    init_db()
    
    # Ensure admin user exists
    from app.services.auth_service import AuthService
    db = SessionLocal()
    try:
        auth = AuthService(db)
        auth.ensure_admin_exists()
    finally:
        db.close()
    
    yield
    # Shutdown: cleanup if needed


app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
    lifespan=lifespan,
)


# Exception handler for redirects
@app.exception_handler(RedirectException)
async def redirect_exception_handler(request: Request, exc: RedirectException):
    return RedirectResponse(url=exc.url, status_code=303)


# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")


# Health check (API)
@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return HealthResponse(status="ok")


# Include routers
from app.routers import advertiser, payments, auth, pages, public_api, oauth

# API routers
app.include_router(auth.router)
app.include_router(oauth.router)  # OAuth для Google, Yandex, VK
app.include_router(advertiser.router)
app.include_router(payments.router)
app.include_router(public_api.router)  # Public API для омниканальности

# HTML pages router (must be last to not override API routes)
app.include_router(pages.router)
