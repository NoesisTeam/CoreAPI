from fastapi import APIRouter, HTTPException
from models.responses import NewClub, UpdateClub
from services.club_service import ClubService, validate_role
from fastapi import APIRouter, Depends, HTTPException

router = APIRouter()
club_service = ClubService()


@router.post("/create")
async def create_club(info: NewClub):
    if not club_service.create_club(info):
        raise HTTPException(status_code=400, detail="Error while creating new club")
    return {"message": "Club created successfully"}

@router.put("/update/{club_id}")
async def update_club(club_id: int, info: UpdateClub, role_name: str = Depends(validate_role)):
    if not club_service.update_club(info, club_id):
        raise HTTPException(status_code=400, detail="Error while updating club")
    return {"message": "Club updated successfully"}

@router.delete("/delete/{club_id}")
async def delete_club(club_id: int, role_name: str = Depends(validate_role)):
    if not club_service.delete_club(club_id):
        raise HTTPException(status_code=400, detail="Error while deleting club")
    return {"message": "Club deleted successfully"}

@router.get("/get/{club_id}")
async def get_club(club_id: int):
    club = club_service.get_club(club_id)
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")
    return club



