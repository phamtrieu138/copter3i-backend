"""
database.py — Cấu hình kết nối MySQL với SQLAlchemy
"""
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from urllib.parse import quote_plus
from config import settings

# URL-encode password để xử lý ký tự đặc biệt như @, #, &, ...
_password = quote_plus(settings.DB_PASSWORD)

# Connection URL cho PyMySQL
DATABASE_URL = (
    f"mysql+pymysql://{settings.DB_USER}:{_password}"
    f"@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
    f"?charset=utf8mb4"
)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,          # Tự động reconnect nếu mất kết nối
    pool_recycle=3600,           # Recycle connection sau 1 giờ
    pool_size=5,
    max_overflow=10,
    echo=settings.DEBUG,         # Log SQL nếu DEBUG=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Dependency injection cho FastAPI routes."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_db_connection() -> bool:
    """Kiểm tra kết nối database có hoạt động không."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
