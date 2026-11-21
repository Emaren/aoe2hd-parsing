"""Restricted historical parser traffic compatibility endpoint.

AoE2WAR's certified public Traffic V2 series is owned outside this legacy
parser. Do not enumerate Firebase users, expose access-log IPs, or mutate
traffic files from an HTTP GET. Retired measurements are UNKNOWN, never zero.
"""
from fastapi import APIRouter, Depends, Header
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from db.db import get_db
from db.models import User
from routes.admin_routes_async import verify_admin_token

router = APIRouter()


@router.get("/api/traffic")
async def get_traffic_stats(
    authorization: str = Header(None),
    x_admin_token: str = Header(None, alias="X-Admin-Token"),
    db: AsyncSession = Depends(get_db),
):
    verify_admin_token(authorization, x_admin_token)
    postgres_total = await db.scalar(select(func.count()).select_from(User))
    return {
        "firebase_total": None,
        "postgres_total": int(postgres_total or 0),
        "mismatch_count": None,
        "only_in_firebase": None,
        "traffic_log": None,
        "summary": None,
        "firebase_status": "RETIRED_UNMEASURED",
        "traffic_status": "UNAVAILABLE_USE_CERTIFIED_TRAFFIC_V2",
    }
