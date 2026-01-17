"""History API Routes."""

from datetime import datetime
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query

from src.presentation.schemas.history import (
    TestRecordResponse,
    TestRecordListResponse,
    StatisticsResponse,
)
from src.presentation.api.dependencies import get_test_record_repository
from src.domain.repositories.test_record_repository import ITestRecordRepository
from src.domain.entities.test_record import TestType

router = APIRouter()


@router.get("/records", response_model=TestRecordListResponse)
async def list_records(
    test_type: str | None = Query(default=None, description="Filter by test type"),
    limit: int = Query(default=50, ge=1, le=100, description="Max records to return"),
    offset: int = Query(default=0, ge=0, description="Offset for pagination"),
    repo: ITestRecordRepository = Depends(get_test_record_repository),
):
    """List test records for the current user."""
    user_id = "anonymous"  # TODO: Get from auth

    # Parse test type if provided
    type_filter = None
    if test_type:
        try:
            type_filter = TestType(test_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid test type: {test_type}")

    records = await repo.list_by_user(
        user_id=user_id,
        test_type=type_filter,
        limit=limit,
        offset=offset,
    )

    total = await repo.count_by_user(user_id=user_id, test_type=type_filter)

    return TestRecordListResponse(
        records=[
            TestRecordResponse(
                id=str(r.id),
                user_id=r.user_id,
                test_type=r.test_type.value,
                provider=r.provider,
                input_text=r.input_text,
                output_text=r.output_text,
                latency_ms=r.latency_ms,
                created_at=r.created_at,
                metadata=r.metadata,
            )
            for r in records
        ],
        total=total,
        limit=limit,
        offset=offset,
        has_more=(offset + len(records)) < total,
    )


@router.get("/records/{record_id}", response_model=TestRecordResponse)
async def get_record(
    record_id: str,
    repo: ITestRecordRepository = Depends(get_test_record_repository),
):
    """Get a specific test record."""
    try:
        uuid_id = UUID(record_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid record ID format")

    record = await repo.get_by_id(uuid_id)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")

    return TestRecordResponse(
        id=str(record.id),
        user_id=record.user_id,
        test_type=record.test_type.value,
        provider=record.provider,
        input_text=record.input_text,
        output_text=record.output_text,
        latency_ms=record.latency_ms,
        created_at=record.created_at,
        metadata=record.metadata,
    )


@router.delete("/records/{record_id}")
async def delete_record(
    record_id: str,
    repo: ITestRecordRepository = Depends(get_test_record_repository),
):
    """Delete a test record."""
    try:
        uuid_id = UUID(record_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid record ID format")

    deleted = await repo.delete(uuid_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Record not found")

    return {"status": "deleted", "id": record_id}


@router.get("/statistics", response_model=StatisticsResponse)
async def get_statistics(
    start_date: datetime | None = Query(default=None, description="Start of period"),
    end_date: datetime | None = Query(default=None, description="End of period"),
    repo: ITestRecordRepository = Depends(get_test_record_repository),
):
    """Get usage statistics for the current user."""
    user_id = "anonymous"  # TODO: Get from auth

    stats = await repo.get_statistics(
        user_id=user_id,
        start_date=start_date,
        end_date=end_date,
    )

    return StatisticsResponse(
        total_tests=stats["total_tests"],
        by_type=stats["by_type"],
        by_provider=stats["by_provider"],
        avg_latency_ms=stats["avg_latency_ms"],
        period_start=start_date,
        period_end=end_date,
    )
