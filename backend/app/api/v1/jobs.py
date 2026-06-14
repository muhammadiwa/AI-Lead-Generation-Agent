"""Agent job monitoring API — track, retry, and manage async jobs."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Job
from app.schemas import APIResponse
from app.core import success_response
from app.core.errors import NotFoundError

router = APIRouter(tags=["Jobs"])


@router.get("/jobs", response_model=APIResponse)
async def list_jobs(
    status: Optional[str] = None,
    job_type: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    """List jobs with optional filters."""
    query = select(Job).order_by(Job.created_at.desc())

    if status:
        query = query.where(Job.status == status)
    if job_type:
        query = query.where(Job.type == job_type)

    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar() or 0

    offset = (page - 1) * limit
    result = await db.execute(query.offset(offset).limit(limit))
    jobs = result.scalars().all()

    return success_response(
        data={
            "jobs": [
                {
                    "id": str(j.id),
                    "type": j.type,
                    "status": j.status,
                    "priority": j.priority,
                    "progress": j.progress,
                    "retry_count": j.retry_count,
                    "error": j.error,
                    "execution_ms": j.execution_ms,
                    "created_at": j.created_at.isoformat() if j.created_at else None,
                    "started_at": j.started_at.isoformat() if j.started_at else None,
                    "completed_at": j.completed_at.isoformat() if j.completed_at else None,
                }
                for j in jobs
            ],
            "total": total,
            "page": page,
            "limit": limit,
        }
    )


@router.get("/jobs/{job_id}", response_model=APIResponse)
async def get_job(job_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Get a single job's details."""
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise NotFoundError("Job", str(job_id))

    return success_response(data={
        "id": str(job.id),
        "type": job.type,
        "status": job.status,
        "priority": job.priority,
        "payload": job.payload,
        "result": job.result,
        "error": job.error,
        "progress": job.progress,
        "retry_count": job.retry_count,
        "max_retries": job.max_retries,
        "worker_id": job.worker_id,
        "execution_ms": job.execution_ms,
        "scheduled_for": job.scheduled_for.isoformat() if job.scheduled_for else None,
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "started_at": job.started_at.isoformat() if job.started_at else None,
        "completed_at": job.completed_at.isoformat() if job.completed_at else None,
    })


@router.post("/jobs/{job_id}/retry", response_model=APIResponse)
async def retry_job(job_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Retry a failed job."""
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise NotFoundError("Job", str(job_id))

    if job.status != "failed":
        return success_response(data={
            "error": f"Cannot retry job in status '{job.status}'. Only failed jobs can be retried."
        })

    if job.retry_count >= job.max_retries:
        return success_response(data={
            "error": f"Job has reached max retries ({job.max_retries}). Cannot retry further."
        })

    job.status = "pending"
    job.error = None
    job.retry_count += 1
    db.add(job)

    return success_response(data={
        "id": str(job.id),
        "status": "pending",
        "retry_count": job.retry_count,
    })


@router.post("/jobs/{job_id}/cancel", response_model=APIResponse)
async def cancel_job(job_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Cancel a pending job."""
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise NotFoundError("Job", str(job_id))

    if job.status != "pending":
        return success_response(data={
            "error": f"Cannot cancel job in status '{job.status}'. Only pending jobs can be cancelled."
        })

    job.status = "cancelled"
    db.add(job)

    return success_response(data={"id": str(job.id), "status": "cancelled"})


@router.get("/jobs/stats", response_model=APIResponse)
async def get_job_stats(db: AsyncSession = Depends(get_db)):
    """Get job statistics summary."""
    total = await db.execute(select(func.count(Job.id)))
    by_status = await db.execute(
        select(Job.status, func.count(Job.id)).group_by(Job.status)
    )
    by_type = await db.execute(
        select(Job.type, func.count(Job.id)).group_by(Job.type)
    )

    return success_response(data={
        "total": total.scalar() or 0,
        "by_status": {row[0]: row[1] for row in by_status.all()},
        "by_type": {row[0]: row[1] for row in by_type.all()},
    })