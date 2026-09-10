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


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    init_firebase_admin()
    print(f"[OK] {settings.APP_NAME} started successfully")
    print("[INFO] API Docs: http://localhost:8001/docs")
    print("[INFO] Admin: http://localhost:8001/admin/analytics/dashboard")
    yield


app = FastAPI(
    title="Yojantra API",
    description="Yojantra - Your intelligent path to government schemes.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
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
raw_origins = settings.CORS_ORIGINS.split(",") if settings.CORS_ORIGINS else []
configured_origins = [origin.strip() for origin in raw_origins if origin.strip()]

is_prod = settings.ENVIRONMENT.lower() in ("production", "prod")
if is_prod:
    # In production, allow strictly configured production origins
    allowed_origins = configured_origins if configured_origins else ["https://schemematch-ai-complete.vercel.app"]
else:
    # In non-production development, include local ports
    allowed_origins = list(dict.fromkeys(LOCAL_DEV_ORIGINS + configured_origins))

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
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
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=(self)"
    response.headers["Content-Security-Policy"] = "default-src 'self'; frame-ancestors 'none';"
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
        "Access-Control-Allow-Headers": "*",
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains"
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
