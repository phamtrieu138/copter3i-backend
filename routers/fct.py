"""
routers/fct.py — API endpoints cho FCT data
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime
from typing import List, Optional

from database import get_db
from models import FCTData
from schemas import (
    FCTInsertRequest,
    FCTBatchInsertRequest,
    FCTInsertResponse,
    InsertResult,
    FCTRecord,
)

router = APIRouter(prefix="/api/fct", tags=["FCT Data"])


# ─── POST /api/fct/insert ──────────────────────────────────────────────────────
@router.post("/insert", response_model=FCTInsertResponse)
def insert_fct_batch(payload: FCTBatchInsertRequest, db: Session = Depends(get_db)):
    """
    Insert kết quả FCT của 1 batch (tối đa 6 board) vào database.
    C# app gọi endpoint này khi kết thúc 1 lần kiểm tra.
    """
    results = []
    success_count = 0

    for item in payload.records:
        try:
            # Bỏ qua board không có serial number
            if not item.seri_no or item.seri_no.strip() == "":
                results.append(InsertResult(
                    seri_no="(empty)",
                    success=False,
                    message="Serial number rỗng, bỏ qua"
                ))
                continue

            record = FCTData(
                SeriNo    = item.seri_no.strip(),
                Vol_5V    = item.vol_5v,
                Vol_15V   = item.vol_15v,
                Speed     = item.speed,
                ErrorCode = item.error_code,
                TestDate  = item.test_date or datetime.now(),
                PO_Num    = item.po_num,
            )
            db.add(record)
            db.flush()  # Lấy ID ngay, chưa commit

            results.append(InsertResult(
                seri_no=item.seri_no,
                success=True,
                message=f"Inserted OK (id={record.id})"
            ))
            success_count += 1

        except Exception as ex:
            results.append(InsertResult(
                seri_no=item.seri_no or "(unknown)",
                success=False,
                message=f"Error: {str(ex)}"
            ))

    # Commit tất cả records thành công trong 1 transaction
    try:
        db.commit()
    except Exception as ex:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database commit failed: {str(ex)}")

    return FCTInsertResponse(
        total=len(payload.records),
        success=success_count,
        failed=len(payload.records) - success_count,
        results=results,
    )


# ─── POST /api/fct/insert-single ──────────────────────────────────────────────
@router.post("/insert-single", response_model=InsertResult)
def insert_fct_single(item: FCTInsertRequest, db: Session = Depends(get_db)):
    """
    Insert 1 record FCT đơn lẻ.
    """
    if not item.seri_no or item.seri_no.strip() == "":
        raise HTTPException(status_code=400, detail="Serial number không được rỗng")

    try:
        record = FCTData(
            SeriNo    = item.seri_no.strip(),
            Vol_5V    = item.vol_5v,
            Vol_15V   = item.vol_15v,
            Speed     = item.speed,
            ErrorCode = item.error_code,
            TestDate  = item.test_date or datetime.now(),
            PO_Num    = item.po_num,
        )
        db.add(record)
        db.commit()
        db.refresh(record)

        return InsertResult(
            seri_no=record.SeriNo,
            success=True,
            message=f"Inserted OK (id={record.id})"
        )
    except Exception as ex:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(ex))


# ─── GET /api/fct/records ─────────────────────────────────────────────────────
@router.get("/records", response_model=List[FCTRecord])
def get_records(
    limit:      int            = Query(100, ge=1, le=1000, description="Số records tối đa"),
    seri_no:    Optional[str]  = Query(None, description="Lọc theo serial number"),
    error_code: Optional[str]  = Query(None, description="Lọc theo mã lỗi (OK / NG_xx)"),
    po_num:     Optional[str]  = Query(None, description="Lọc theo Production Order Number"),
    db: Session = Depends(get_db)
):
    """
    Lấy danh sách records FCT (mới nhất trước).
    Hỗ trợ filter: seri_no, error_code, po_num.
    """
    query = db.query(FCTData).order_by(desc(FCTData.TestDate))

    if seri_no:
        query = query.filter(FCTData.SeriNo.like(f"%{seri_no}%"))
    if error_code:
        query = query.filter(FCTData.ErrorCode == error_code)
    if po_num:
        query = query.filter(FCTData.PO_Num.like(f"%{po_num}%"))

    records = query.limit(limit).all()

    return [
        FCTRecord(
            id         = r.id,
            seri_no    = r.SeriNo,
            vol_5v     = r.Vol_5V,
            vol_15v    = r.Vol_15V,
            speed      = r.Speed,
            error_code = r.ErrorCode,
            test_date  = r.TestDate,
            po_num     = r.PO_Num,
        )
        for r in records
    ]


# ─── GET /api/fct/stats ───────────────────────────────────────────────────────
@router.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    """
    Thống kê tổng quan: tổng số test, OK, NG.
    """
    total = db.query(FCTData).count()
    ok    = db.query(FCTData).filter(FCTData.ErrorCode == "OK").count()
    ng    = total - ok

    return {
        "total": total,
        "ok":    ok,
        "ng":    ng,
        "pass_rate": f"{(ok / total * 100):.1f}%" if total > 0 else "N/A"
    }
