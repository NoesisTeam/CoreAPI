from fastapi import APIRouter, HTTPException
from services.club_service import ClubService

router = APIRouter()

club_service = ClubService()


@router.post("/create")
async def register_user():
    return 0

