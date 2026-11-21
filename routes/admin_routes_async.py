from fastapi import APIRouter, Depends, HTTPException, Header, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from db.models import User
from db.db import get_async_session
from datetime import datetime
from sqlalchemy import desc
import os
import secrets

router = APIRouter(prefix="/api/admin", tags=["Admin"])

# ───────────────────────────────────────────────
# 🔐 Admin Token Verification (supports both headers)
# ───────────────────────────────────────────────
def verify_admin_token(
    authorization: str = Header(None),
    x_admin_token: str = Header(None, alias="x-admin-token"),
):
    """Require an explicitly provisioned server-side credential for admin access.

    There must be no built-in fallback credential: a missing configuration fails
    closed instead of treating a public source literal as the admin secret.
    """
    expected = os.getenv("ADMIN_TOKEN")
    if not expected or not expected.strip():
        raise HTTPException(status_code=503, detail="Admin authentication unavailable")

    token = x_admin_token
    if not token and authorization:
        scheme, separator, value = authorization.partition(" ")
        if scheme.lower() == "bearer" and separator:
            token = value.strip()

    if not token or len(token) > 512 or not secrets.compare_digest(token, expected):
        raise HTTPException(status_code=401, detail="Unauthorized")

@router.get("/users")
async def list_users(
    authorization: str = Header(None),
    x_admin_token: str = Header(None, alias="X-Admin-Token"),
    session: AsyncSession = Depends(get_async_session),
):
    verify_admin_token(authorization, x_admin_token)
    result = await session.execute(select(User).order_by(desc(User.created_at)))
    users = result.scalars().all()
    return [u.to_dict() for u in users]

# ───────────────────────────────────────────────
# 🔄 Mark User Online (last seen)
# ───────────────────────────────────────────────
@router.post("/user/online")
async def mark_user_online(
    payload: dict = Body(...),
    authorization: str = Header(None),
    x_admin_token: str = Header(None, alias="X-Admin-Token"),
    session: AsyncSession = Depends(get_async_session),
):
    verify_admin_token(authorization, x_admin_token)
    uid = payload.get("uid")
    if not uid:
        raise HTTPException(status_code=400, detail="Missing UID")

    result = await session.execute(select(User).where(User.uid == uid))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.last_seen = datetime.utcnow()
    await session.commit()
    return {"message": "User marked online", "last_seen": user.last_seen.isoformat()}

# ───────────────────────────────────────────────
# ❌ Delete User by UID (Admin only)
# ───────────────────────────────────────────────
@router.delete("/delete_user/{uid}")
async def delete_user(
    uid: str,
    authorization: str = Header(None),
    x_admin_token: str = Header(None, alias="X-Admin-Token"),
    session: AsyncSession = Depends(get_async_session),
):
    verify_admin_token(authorization, x_admin_token)

    result = await session.execute(select(User).where(User.uid == uid))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    await session.delete(user)
    await session.commit()
    return {"message": f"Deleted user {uid}"}
