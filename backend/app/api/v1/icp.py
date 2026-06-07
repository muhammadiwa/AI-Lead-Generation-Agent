"""ICP (Ideal Customer Profile) API endpoints."""
from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import ICPProfile, ICPFilter
from app.schemas import (
    APIResponse,
    ICPFilterCreate,
    ICPProfileCreate,
    ICPProfileResponse,
    success_response,
)
from app.core.errors import NotFoundError

router = APIRouter(tags=["ICP"])


@router.post("/icp", response_model=APIResponse, status_code=201)
async def create_icp_profile(profile: ICPProfileCreate, db: AsyncSession = Depends(get_db)):
    """Create an ICP profile with filters."""
    icp = ICPProfile(name=profile.name, description=profile.description)
    db.add(icp)
    await db.flush()

    for filter_data in profile.filters:
        icp_filter = ICPFilter(
            icp_profile_id=icp.id,
            filter_type=filter_data.filter_type,
            filter_key=filter_data.filter_key,
            filter_value=filter_data.filter_value,
            operator=filter_data.operator,
            weight=filter_data.weight,
        )
        db.add(icp_filter)

    return success_response(
        data=ICPProfileResponse.model_validate(icp),
        meta={"created": True},
    )


@router.get("/icp", response_model=APIResponse)
async def list_icp_profiles(db: AsyncSession = Depends(get_db)):
    """List all ICP profiles."""
    result = await db.execute(select(ICPProfile).order_by(ICPProfile.created_at.desc()))
    profiles = result.scalars().all()

    return success_response(
        data=[
            {
                "id": p.id,
                "name": p.name,
                "description": p.description,
                "is_active": p.is_active,
                "created_at": p.created_at.isoformat() if p.created_at else None,
            }
            for p in profiles
        ]
    )


@router.patch("/icp/{profile_id}", response_model=APIResponse)
async def update_icp_profile(
    profile_id: uuid.UUID,
    name: Optional[str] = None,
    description: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
):
    """Update an ICP profile."""
    result = await db.execute(select(ICPProfile).where(ICPProfile.id == profile_id))
    profile = result.scalar_one_or_none()
    if not profile:
        raise NotFoundError("ICPProfile", str(profile_id))

    if name:
        profile.name = name
    if description is not None:
        profile.description = description
    if is_active is not None:
        profile.is_active = is_active

    db.add(profile)
    return success_response(data=ICPProfileResponse.model_validate(profile))


@router.delete("/icp/{profile_id}", response_model=APIResponse)
async def delete_icp_profile(profile_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Delete an ICP profile."""
    result = await db.execute(select(ICPProfile).where(ICPProfile.id == profile_id))
    profile = result.scalar_one_or_none()
    if not profile:
        raise NotFoundError("ICPProfile", str(profile_id))

    await db.delete(profile)
    return success_response(data={"id": profile_id, "deleted": True})