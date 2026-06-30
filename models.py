"""
models.py — SQLAlchemy ORM models (ánh xạ đến bảng MySQL)
"""
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from database import Base


class FCTData(Base):
    """
    Bảng lưu kết quả kiểm tra FCT của từng board quạt.
    Tương ứng với INSERT trong Form1.cs → SaveToDb()
    """
    __tablename__ = "FCTData"

    id        = Column(Integer, primary_key=True, autoincrement=True)
    SeriNo    = Column(String(100), nullable=False, comment="Serial number của quạt")
    Vol_5V    = Column(String(20),  nullable=True,  comment="Điện áp 5V đo được")
    Vol_15V   = Column(String(20),  nullable=True,  comment="Điện áp 15V đo được")
    Speed     = Column(String(20),  nullable=True,  comment="Tốc độ quạt (RPM)")
    ErrorCode = Column(String(50),  nullable=True,  comment="Mã lỗi: OK hoặc NG_xx")
    TestDate  = Column(DateTime,    nullable=True,  server_default=func.now(), comment="Thời điểm kiểm tra")
