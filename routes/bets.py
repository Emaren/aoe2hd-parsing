"""Legacy demonstration betting endpoints, never financial or custody authority.

The real FINANCIAL system's seven gates remain HOLD. No demo bet should be
recorded as accepted, settled, or pending in a production API response.
"""
from fastapi import APIRouter, HTTPException

router = APIRouter()


def _financial_unavailable():
    raise HTTPException(
        status_code=503,
        detail="Legacy demo betting disabled; financial authorization not active",
    )


@router.post("/bets/create")
def create_bet():
    _financial_unavailable()


@router.post("/bets/accept/{match_id}")
def accept_bet(match_id: str):
    _financial_unavailable()


@router.get("/bets/pending")
def get_pending_bets():
    _financial_unavailable()


@router.post("/replay/upload/{match_id}")
async def upload_replay(match_id: str):
    _financial_unavailable()
