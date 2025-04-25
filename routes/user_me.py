from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from firebase_admin import auth

from db.db import get_db
from db.models import User

router = APIRouter(
    prefix="/api/user",
    tags=["user"]
)

# ───────────────────────────────────────────────
# 🔐 Firebase Auth + FastAPI Dependency
# ───────────────────────────────────────────────
auth_scheme = HTTPBearer()

async def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(auth_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    try:
        decoded = auth.verify_id_token(creds.credentials)
        uid = decoded["uid"]
        result = await db.execute(select(User).where(User.uid == uid))
        user = result.scalars().first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")

# ───────────────────────────────────────────────
# 🧾 Manual Fallback API for Debug
# ───────────────────────────────────────────────
class UserMeRequest(BaseModel):
    uid: str | None = None
    email: str | None = None

@router.post("/me")
async def get_user_me(data: UserMeRequest, db_gen=Depends(get_db)):
    print(f"🔎 Received data: {data}")
    async with db_gen as db:
        user = None

        if data.uid:
            result = await db.execute(select(User).where(User.uid == data.uid))
            user = result.scalar_one_or_none()

        if not user and data.email:
            result = await db.execute(select(User).where(User.email == data.email))
            user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        return user.to_dict()

__all__ = ["get_current_user"]
