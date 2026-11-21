"""Legacy Firebase account endpoints.

The active AoE2WAR website authenticates its own site sessions. No authenticated
mapping exists from Firebase UID to a site account. Legacy mutable endpoints
therefore fail closed and never create or mutate a user based on a client UID.
The historical user rows are not deleted or re-keyed.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from db.db import get_db
from db.models import User

router = APIRouter(prefix="/api/user", tags=["user"])


def legacy_identity_retired():
    raise HTTPException(
        status_code=status.HTTP_410_GONE,
        detail="Legacy Firebase account authentication retired; use the AoE2WAR site session",
    )


@router.post("/me")
async def legacy_signup_retired():
    legacy_identity_retired()


@router.post("/update_name")
async def legacy_name_change_retired():
    legacy_identity_retired()


@router.post("/update_wallet")
async def legacy_wallet_change_retired():
    legacy_identity_retired()


@router.get("/online")
async def get_online_users(db: AsyncSession = Depends(get_db)):
    # Compatibility-only public read; no migration of Firebase UID ownership.
    result = await db.execute(
        select(User).where(User.in_game_name.isnot(None)).order_by(desc(User.last_seen))
    )
    users = result.scalars().all()
    return [
        {"uid": u.uid, "in_game_name": u.in_game_name, "verified": u.verified}
        for u in users
    ]


@router.get("/online_users")
async def get_online_users_alias(db: AsyncSession = Depends(get_db)):
    return await get_online_users(db)
