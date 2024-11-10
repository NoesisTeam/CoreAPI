from fastapi import APIRouter, Depends, HTTPException
from models.responses import NewClub, UpdateClub, NewParticipant, UserID
from services.club_service import ClubService, get_token_club

club_router = APIRouter(prefix="/club", tags=["Club"])
club_service = ClubService()

def validate_role_in_club(rolename:str):
    return rolename == "Founder"

@club_router.post("/create")
async def create_club(info: NewClub):
    if not club_service.create_club(info):
        raise HTTPException(status_code=400, detail="Error while creating new club")
    return {"message": "Club created successfully"}

@club_router.put("/update")
async def update_club(info: UpdateClub,
                      token: dict = Depends(get_token_club)):
    if validate_role_in_club(token.get("role")):
        club_service.update_club(info, token.get("club"))
        return {"message": "Club updated successfully"}
    else:
        raise HTTPException(status_code=401, detail="You are not authorized to update this club")

@club_router.put("/delete/")
async def delete_club(token: dict = Depends(get_token_club)):
    if validate_role_in_club(token.get("role")):
        club_service.delete_club(token.get("club"))
        return {"message": "Club deleted successfully"}
    else:
        raise HTTPException(status_code=401, detail="You are not authorized to delete this club")

@club_router.get("/get/{club_id}")
async def get_club(club_id: int):
    club = club_service.get_club(club_id)
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")
    return club


@club_router.get("/get/all")
async def get_all_clubs():
    return club_service.get_all_clubs()

@club_router.get("/get/founded/{user_id}", summary="List clubs where the user is the founder")
async def get_founded_clubs(user_id: int):
    return club_service.get_founded_clubs(user_id)

@club_router.get("/get/joined/{user_id}", summary="List clubs where the user is a member")
async def get_joined_clubs(user_id: int):
    return club_service.get_joined_clubs(user_id)

@club_router.post("/add_member")
async def add_member(new_member: NewParticipant):
    if not club_service.add_member(new_member.id_club, new_member.id_user):
        raise HTTPException(status_code=400, detail="Error while adding member")
    return {"message": "Member added successfully"}

#request to join
@club_router.post("/membership/request")
async def request_membership(new_member: NewParticipant):
    if not club_service.request_membership(new_member.id_club, new_member.id_user):
        raise HTTPException(status_code=400, detail="Error while requesting membership")
    return {"message": "Membership requested successfully"}

@club_router.patch("/membership/approve")
async def approve_membership(membership: UserID, token: dict = Depends(get_token_club)):
    if validate_role_in_club(token.get("role")):
        club_service.approve_membership(token.get("club"), membership.id_user)
        return {"message": "Membership approved successfully"}
    else:
        raise HTTPException(status_code=401, detail="You are not authorized to approve membership")


@club_router.patch("/membership/reject")
async def reject_membership(membership: UserID, token: dict = Depends(get_token_club)):
    if validate_role_in_club(token.get("role")):
        club_service.reject_membership(token.get("club"), membership.id_user)
        return {"message": "Membership rejected successfully"}
    else:
        raise HTTPException(status_code=401, detail="You are not authorized to reject membership")

@club_router.patch("/membership/remove")
async def remove_member(membership: UserID, token: dict = Depends(get_token_club)):
    if validate_role_in_club(token.get("role")):
        club_service.remove_member(token.get("club"), membership.id_user)
        return {"message": "Member removed successfully"}
    else:
        raise HTTPException(status_code=401, detail="You are not authorized to remove this member")

@club_router.delete("/membership/leave")
async def leave_club():
    if not club_service.leave_club:
        raise HTTPException(status_code=400, detail="Error while leaving club")
    return {"message": "Left club successfully"}




