"""
schemas.py — Pydantic schemas cho request/response validation
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List


# ─── Request schemas ───────────────────────────────────────────────────────────

class FCTInsertRequest(BaseModel):
    """
    Dữ liệu gửi từ C# app khi lưu kết quả 1 board quạt.
    Tương ứng với 1 row INSERT INTO FCTData
    """
    seri_no:    str            = Field(...,  description="Serial number của quạt", example="COP3I-001")
    vol_5v:     Optional[str]  = Field(None, description="Điện áp 5V", example="4.98V")
    vol_15v:    Optional[str]  = Field(None, description="Điện áp 15V", example="14.95V")
    speed:      Optional[str]  = Field(None, description="Tốc độ RPM", example="270")
    error_code: Optional[str]  = Field(None, description="OK hoặc NG_xx", example="OK")
    test_date:  Optional[datetime] = Field(None, description="Thời điểm test, nếu None sẽ dùng server time")


class FCTBatchInsertRequest(BaseModel):
    """
    Gửi 6 board cùng lúc (1 batch = 1 lần nhấn Save trong JIG app).
    """
    records: List[FCTInsertRequest] = Field(..., description="Danh sách kết quả 6 quạt")


# ─── Response schemas ──────────────────────────────────────────────────────────

class InsertResult(BaseModel):
    seri_no: str
    success: bool
    message: str


class FCTInsertResponse(BaseModel):
    total:   int
    success: int
    failed:  int
    results: List[InsertResult]


class HealthResponse(BaseModel):
    status:   str
    database: str
    version:  str = "1.0.0"


class FCTRecord(BaseModel):
    id:         int
    seri_no:    str
    vol_5v:     Optional[str]
    vol_15v:    Optional[str]
    speed:      Optional[str]
    error_code: Optional[str]
    test_date:  Optional[datetime]

    class Config:
        from_attributes = True
