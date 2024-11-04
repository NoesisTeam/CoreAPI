from fastapi import APIRouter, HTTPException
from models.responses import NewClub
from services.club_service import ClubService

router = APIRouter()
club_service = ClubService()


@router.post("/create")
async def create_club(info: NewClub):
    if not club_service.create_club(info):
        raise HTTPException(status_code=400, detail="Error while creating new club")
    return {"message": "Club created successfully"}



