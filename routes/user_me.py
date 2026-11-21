"""Compatibility-only legacy account boundary; no Firebase/site-cookie bridge."""
from fastapi import APIRouter, HTTPException, status

router = APIRouter(prefix="/api/user", tags=["user"])


async def get_current_user():
    # Caller-supplied Firebase UIDs must never become AoE2WAR signed-site identities.
    # This dependency remains explicit so old replay/heartbeat handlers fail closed.
    raise HTTPException(
        status_code=status.HTTP_410_GONE,
        detail="Legacy Firebase token login retired; no site-account mapping is authorized",
    )


@router.get("/me")
async def legacy_get_me_retired():
    await get_current_user()
