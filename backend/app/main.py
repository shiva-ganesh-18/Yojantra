"""SchemeMatch AI - Main FastAPI Application."""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time

from app.core.database import init_db
from app.routers import (
    auth, users, schemes, matches, applications, 
    chat, admin, documents, notifications, csc
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    print("[OK] SchemeMatch AI started successfully")
    print("[INFO] API Docs: http://localhost:8000/docs")
    print("[INFO] Admin: http://localhost:8000/admin/analytics/dashboard")
    yield


app = FastAPI(
    title="SchemeMatch AI",
    description="AI-driven government scheme matching for marginalized entrepreneurs",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "message": str(exc)}
    )


@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "schemematch-ai", "version": "1.0.0"}


# Include all routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(schemes.router)
app.include_router(matches.router)
app.include_router(applications.router)
app.include_router(chat.router)
app.include_router(admin.router)
app.include_router(documents.router)
app.include_router(notifications.router)
app.include_router(csc.router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
