"""
main.py — Entry point của FastAPI backend
Copter3i JIG - FCT Data API
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import os

from config import settings
from database import Base, engine, test_db_connection
from routers import fct
from schemas import HealthResponse
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from backup import perform_backup

# ─── Logging setup ────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("copter3i")


# ─── App lifecycle ────────────────────────────────────────────────────────────
scheduler = AsyncIOScheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Chạy khi startup: tạo bảng nếu chưa có, kiểm tra DB."""
    logger.info("=== Copter3i Backend Starting ===")
    
    # Tự động tạo bảng FCTData nếu chưa tồn tại
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables verified/created OK")
    except Exception as e:
        logger.error(f"Failed to create tables: {e}")

    # Test connection
    if test_db_connection():
        logger.info("Database connection: OK")
    else:
        logger.warning("Database connection: FAILED — API will start but DB calls will fail")

    # Setup automatic daily backup
    scheduler.add_job(perform_backup, 'cron', hour=2, minute=0) # Backup at 02:00 AM daily
    scheduler.start()
    logger.info("Backup scheduler started: daily at 02:00 AM")

    yield  # App đang chạy

    scheduler.shutdown()
    logger.info("=== Copter3i Backend Shutting Down ===")


# ─── FastAPI App ───────────────────────────────────────────────────────────────
app = FastAPI(
    title="Copter3i JIG Backend API",
    description=(
        "Backend API cho JIG kiểm tra quạt Copter3i.\n\n"
        "Nhận kết quả FCT từ C# app và lưu vào MySQL trên VPN server."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",       # Swagger UI
    redoc_url="/redoc",     # ReDoc UI
)

# ─── CORS (cho phép C# app gọi từ bất kỳ IP nào trong VPN) ───────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # Trong production có thể giới hạn IP
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("updates", exist_ok=True)
app.mount("/updates", StaticFiles(directory="updates"), name="updates")


# ─── Global exception handler ─────────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {str(exc)}"}
    )


# ─── Health check endpoint ────────────────────────────────────────────────────
@app.get("/api/health", response_model=HealthResponse, tags=["System"])
def health_check():
    """
    Kiểm tra trạng thái server và database.
    C# app gọi endpoint này mỗi 2 giây để update lblDatabaseConnection.
    """
    db_ok = test_db_connection()
    return HealthResponse(
        status="ok",
        database="connected" if db_ok else "disconnected",
    )


@app.get("/", tags=["System"])
def root():
    return {
        "service": "Copter3i JIG Backend",
        "version": "1.0.0",
        "docs":    "/docs",
        "health":  "/api/health",
    }


# ─── Register routers ─────────────────────────────────────────────────────────
app.include_router(fct.router)


# ─── Run trực tiếp (development) ─────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=settings.DEBUG,
        log_level="debug" if settings.DEBUG else "info",
    )
