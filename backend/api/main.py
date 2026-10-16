"""
api/main.py

FastAPI application factory for Clinora backend.

Responsibilities:
- Create and configure the FastAPI app instance.
- Register middleware (correlation ID).
- Register exception handlers (domain exception → HTTP response mapping).
- Register API routers.
- Configure CORS.
- Configure startup/shutdown lifecycle events.

Non-goals:
- Does not contain business logic.
- Does not issue database queries.
- Does not configure infrastructure (DB engine is created lazily on first use).
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import auth, health
from core.config import settings
from core.errors import (
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    NotFoundError,
    TokenReuseError,
    ValidationError,
    authentication_handler,
    authorization_handler,
    conflict_handler,
    domain_validation_handler,
    generic_error_handler,
    not_found_handler,
)
from core.logging import configure_logging
from core.middleware import CorrelationIDMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Configure logging on startup."""
    log_level = "DEBUG" if settings.is_development else "INFO"
    configure_logging(level=log_level)
    yield
    # Shutdown: close DB engine, flush logs, etc. (expanded in later phases)


def create_app() -> FastAPI:
    app = FastAPI(
        title="Clinora API",
        description=(
            "AI-Assisted Clinical Management, Longitudinal Patient Record "
            "& Clinical Insights Platform"
        ),
        version="0.1.0",
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
        lifespan=lifespan,
    )

    # --- Middleware (outermost first) ---
    app.add_middleware(CorrelationIDMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,   # Required for cookie-based refresh tokens
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"],
    )

    # --- Exception handlers ---
    app.add_exception_handler(NotFoundError, not_found_handler)  # type: ignore[arg-type]
    app.add_exception_handler(ConflictError, conflict_handler)  # type: ignore[arg-type]
    # TokenReuseError extends AuthenticationError — register it first so it
    # takes precedence before the broader AuthenticationError handler.
    app.add_exception_handler(TokenReuseError, authentication_handler)  # type: ignore[arg-type]
    app.add_exception_handler(AuthenticationError, authentication_handler)  # type: ignore[arg-type]
    app.add_exception_handler(AuthorizationError, authorization_handler)  # type: ignore[arg-type]
    app.add_exception_handler(ValidationError, domain_validation_handler)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, generic_error_handler)

    # --- Routers ---
    app.include_router(health.router)
    app.include_router(auth.router, prefix="/api/v1")

    return app


app = create_app()
