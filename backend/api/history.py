"""历史记录CRUD路由"""

from __future__ import annotations

import json
import math

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas import (
    ApiResponse,
    HistoryListResponse,
    HistoryRecordResponse,
    HistorySaveRequest,
)
from db.database import get_db
from models.divination_record import DivinationRecord

router = APIRouter(prefix="/api/history", tags=["history"])


def _record_to_response(record: DivinationRecord) -> HistoryRecordResponse:
    return HistoryRecordResponse(
        id=record.id,
        question=record.question,
        method=record.method,
        hexagram_name=record.hexagram_name,
        fortune=record.fortune,
        created_at=record.created_at.isoformat(),
        hexagram_data=json.loads(record.hexagram_data),
        changed_hexagram_data=json.loads(record.changed_hexagram_data)
        if record.changed_hexagram_data
        else None,
        analysis_data=json.loads(record.analysis_data),
    )


@router.post("/")
async def save_history(request: HistorySaveRequest, db: AsyncSession = Depends(get_db)):
    """保存占卜记录"""
    record = DivinationRecord(
        question=request.question,
        method=request.method,
        hexagram_data=json.dumps(request.hexagram_data, ensure_ascii=False),
        changed_hexagram_data=json.dumps(request.changed_hexagram_data, ensure_ascii=False)
        if request.changed_hexagram_data
        else None,
        analysis_data=json.dumps(request.analysis_data, ensure_ascii=False),
        fortune=request.analysis_data.get("fortune", "未知"),
        hexagram_name=request.hexagram_data.get("name", "未知"),
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return ApiResponse(success=True, data={"id": record.id})


@router.get("/")
async def list_history(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """获取历史记录列表"""
    count_result = await db.execute(select(func.count(DivinationRecord.id)))
    total = count_result.scalar() or 0

    offset = (page - 1) * limit
    result = await db.execute(
        select(DivinationRecord)
        .order_by(DivinationRecord.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    records = result.scalars().all()

    return ApiResponse(
        success=True,
        data=HistoryListResponse(
            records=[_record_to_response(r) for r in records],
            total=total,
            page=page,
            limit=limit,
            total_pages=max(1, math.ceil(total / limit)),
        ).model_dump(),
    )


@router.get("/{record_id}")
async def get_history_record(record_id: int, db: AsyncSession = Depends(get_db)):
    """获取单条历史记录"""
    result = await db.execute(
        select(DivinationRecord).where(DivinationRecord.id == record_id)
    )
    record = result.scalar_one_or_none()
    if not record:
        return ApiResponse(success=False, error="记录不存在")
    return ApiResponse(success=True, data=_record_to_response(record).model_dump())


@router.delete("/{record_id}")
async def delete_history_record(record_id: int, db: AsyncSession = Depends(get_db)):
    """删除历史记录"""
    result = await db.execute(
        select(DivinationRecord).where(DivinationRecord.id == record_id)
    )
    record = result.scalar_one_or_none()
    if not record:
        return ApiResponse(success=False, error="记录不存在")
    await db.delete(record)
    await db.commit()
    return ApiResponse(success=True)
