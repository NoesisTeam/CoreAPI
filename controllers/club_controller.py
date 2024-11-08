from fastapi import APIRouter, Depends, HTTPException
from models.responses import NewClub, UpdateClub, NewParticipant
from services.club_service import ClubService, validate_role

club_router = APIRouter(prefix="/club", tags=["Club"])
club_service = ClubService()

def validate_role_in_club(tk_info: str, club_id: int):
    tk_role_name = tk_info.split(":::")[0]
    tk_club_id = int(tk_info.split(":::")[1])
    if tk_role_name == "Founder" and tk_club_id == club_id:
        return True
    else:
        return False

@club_router.post("/create")
async def create_club(info: NewClub):
    if not club_service.create_club(info):
        raise HTTPException(status_code=400, detail="Error while creating new club")
    return {"message": "Club created successfully"}

@club_router.put("/update/{club_id}")
async def update_club(club_id: int,
                      info: UpdateClub,
                      tk_info: str = Depends(validate_role)):
    if validate_role_in_club(tk_info, club_id):
        club_service.update_club(info, club_id)
        return {"message": "Club updated successfully"}
    else:
        raise HTTPException(status_code=401, detail="You are not authorized to update this club")

@club_router.put("/delete/{club_id}")
async def delete_club(club_id: int,
                      tk_info: str = Depends(validate_role)):
    if validate_role_in_club(tk_info, club_id):
        club_service.delete_club(club_id)
        return {"message": "Club deleted successfully"}
    else:
        raise HTTPException(status_code=401, detail="You are not authorized to delete this club")

@club_router.get("/get/{club_id}")
async def get_club(club_id: int):
    club = club_service.get_club(club_id)
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")
    return club


@club_router.get("/get_all")
async def get_all_clubs():
    return club_service.get_all_clubs()

@club_router.get("/founded/{user_id}", summary="List clubs where the user is the founder")
async def get_founded_clubs(user_id: int):
    return club_service.get_founded_clubs(user_id)

@club_router.get("/joined/{user_id}", summary="List clubs where the user is a member")
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
async def approve_membership(new_member: NewParticipant, tk_info: str = Depends(validate_role)):
    if validate_role_in_club(tk_info, new_member.id_club):
        club_service.approve_membership(new_member.id_club, new_member.id_user)
        return {"message": "Membership approved successfully"}
    else:
        raise HTTPException(status_code=401, detail="You are not authorized to approve membership")


@club_router.patch("/membership/reject")
async def reject_membership(club_id: int, user_id: int, role_name: str = Depends(validate_role)):
    if not club_service.reject_membership(club_id, user_id):
        raise HTTPException(status_code=400, detail="Error while rejecting membership")
    return {"message": "Membership rejected successfully"}

@club_router.delete("/membership/{club_id}/remove/{user_id}")
async def remove_member(club_id: int, user_id: int, role_name: str = Depends(validate_role)):
    if not club_service.remove_member(club_id, user_id):
        raise HTTPException(status_code=400, detail="Error while removing member")
    return {"message": "Member removed successfully"}

@club_router.delete("/membership/leave")
async def leave_club():
    if not club_service.leave_club:
        raise HTTPException(status_code=400, detail="Error while leaving club")
    return {"message": "Left club successfully"}




