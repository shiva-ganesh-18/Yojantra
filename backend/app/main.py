"""Yojantra - Main FastAPI Application.
Intelligent GovTech platform matching marginalized entrepreneurs to government schemes.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time

from app.core.config import get_settings
from app.core.database import init_db
from app.core.firebase import init_firebase_admin
from app.routers import (
    auth, users, schemes, matches, applications, 
    chat, admin, documents, notifications, csc,
    locations, institutions, integrations, locales
)

settings = get_settings()


# Strengthened Content-Security-Policy for a JSON API backend.
# cdn.jsdelivr.net is allowlisted for scripts/styles ONLY so the FastAPI
# Swagger/ReDoc developer docs (dev/test) keep rendering; no application
# endpoint serves HTML/JS itself. No wildcard sources anywhere.
CONTENT_SECURITY_POLICY = (
    "default-src 'self'; "
    "script-src 'self' https://cdn.jsdelivr.net; "
    "style-src 'self' https://cdn.jsdelivr.net; "
    "img-src 'self' data: https:; "
    "font-src 'self' https:; "
    "connect-src 'self'; "
    "object-src 'none'; "
    "base-uri 'self'; "
    "form-action 'self'; "
    "frame-ancestors 'none'"
)
PERMISSIONS_POLICY = "camera=(), microphone=(), geolocation=(self)"
REFERRER_POLICY = "strict-origin-when-cross-origin"


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    init_firebase_admin()
    print(f"[OK] {settings.APP_NAME} started successfully")
    print("[INFO] API Docs: http://localhost:8001/docs")
    print("[INFO] Admin: http://localhost:8001/admin/analytics/dashboard")
    yield


is_prod_boot = settings.ENVIRONMENT.lower() in ("production", "prod")

app = FastAPI(
    title="Yojantra API",
    description="Yojantra - Your intelligent path to government schemes.",
    version="1.0.0",
    # API docs stay available for development/testing; disabled in production.
    docs_url=None if is_prod_boot else "/docs",
    redoc_url=None if is_prod_boot else "/redoc",
    lifespan=lifespan
)

# Secure CORS configuration
LOCAL_DEV_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
    "http://localhost:5175",
    "http://127.0.0.1:5175",
]

# Explicit safe request-header allowlist (replaces wildcard; credentials stay
# enabled only against these explicit origins, never "*").
SAFE_ALLOW_HEADERS = [
    "Authorization",
    "Content-Type",
    "Accept",
    "Origin",
    "X-Requested-With",
    "X-Firebase-AppCheck",
    "X-Signature",
    "X-Timestamp",
]


def _is_loopback_origin(origin: str) -> bool:
    """True for localhost/loopback origins that must never be trusted in production."""
    host = (origin or "").strip().lower().split("://", 1)[-1].split("/", 1)[0].split("@")[-1]
    if host.startswith("["):
        host = host.split("]", 1)[0] + "]"  # bracketed IPv6, drop port
    else:
        host = host.split(":")[0]  # drop port
    return host in ("localhost", "127.0.0.1", "[::1]", "::1", "0.0.0.0") or host.endswith(".localhost")


raw_origins = settings.CORS_ORIGINS.split(",") if settings.CORS_ORIGINS else []
configured_origins = [origin.strip() for origin in raw_origins if origin.strip()]

is_prod = is_prod_boot
if is_prod:
    # In production, allow strictly configured production origins; loopback
    # origins are stripped even if present in configuration.
    allowed_origins = [o for o in configured_origins if not _is_loopback_origin(o)]
    if not allowed_origins:
        allowed_origins = ["https://schemematch-ai-complete.vercel.app"]
else:
    # In non-production development, include local ports
    allowed_origins = list(dict.fromkeys(LOCAL_DEV_ORIGINS + configured_origins))

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=SAFE_ALLOW_HEADERS,
    expose_headers=["X-Process-Time"],
)


@app.middleware("http")
async def add_security_and_timing_headers(request: Request, call_next):
    start_time = time.time()

    # App Check Protection (when enabled in settings)
    if settings.FIREBASE_APP_CHECK_ENFORCEMENT and request.method != "OPTIONS":
        # Bypass health and docs endpoints
        path = request.url.path
        if not (path.startswith("/docs") or path.startswith("/redoc") or path.startswith("/openapi.json") or path in ("/health", "/api/health")):
            from app.core.firebase import verify_app_check_token, InvalidFirebaseTokenError
            app_check_token = request.headers.get("X-Firebase-AppCheck")
            try:
                verify_app_check_token(app_check_token)
            except InvalidFirebaseTokenError as err:
                return JSONResponse(
                    status_code=403,
                    content={"detail": "Forbidden: Invalid or missing Firebase App Check token", "error": str(err)}
                )

    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = f"{process_time:.4f}s"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = REFERRER_POLICY
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Permissions-Policy"] = PERMISSIONS_POLICY
    response.headers["Content-Security-Policy"] = CONTENT_SECURITY_POLICY
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    import traceback
    if getattr(settings, "DEBUG", False):
        traceback.print_exc()
        error_msg = str(exc)
    else:
        error_msg = "An unexpected error occurred. Please try again later."

    origin = request.headers.get("origin")
    cors_origin = origin if (origin and origin in allowed_origins) else (allowed_origins[0] if allowed_origins else "*")
    headers = {
        "Access-Control-Allow-Origin": cors_origin,
        "Access-Control-Allow-Credentials": "true",
        "Access-Control-Allow-Methods": "GET, POST, PUT, PATCH, DELETE, OPTIONS",
        "Access-Control-Allow-Headers": ", ".join(SAFE_ALLOW_HEADERS),
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "Referrer-Policy": REFERRER_POLICY,
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "X-XSS-Protection": "1; mode=block",
        "Permissions-Policy": PERMISSIONS_POLICY,
        "Content-Security-Policy": CONTENT_SECURITY_POLICY,
    }
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "message": error_msg},
        headers=headers
    )


@app.get("/health")
@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": "yojantra-api",
        "product": "Yojantra",
        "version": "1.0.0"
    }


# Include all routers at both root and /api prefix for full client/proxy compatibility
api_routers = [
    auth.router, users.router, matches.router, schemes.router,
    applications.router, chat.router, admin.router, documents.router,
    notifications.router, csc.router, locations.router, institutions.router,
    integrations.router, locales.router
]

for r in api_routers:
    app.include_router(r)
    app.include_router(r, prefix="/api")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
