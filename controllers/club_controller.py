from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form

from models.responses import NewClub, UpdateClub, NewParticipant, UserID, ResourceToUpload
from services import quiz_service
from services.club_service import ClubService, get_token_club
from services.quiz_service import QuizService
from services.resource_service import ResourceService

club_router = APIRouter(prefix="/club", tags=["Club"])
club_service = ClubService()
resource_service = ResourceService()
quiz_service = QuizService()

def validate_founder_role(rolename:str):
    return rolename == "Founder"

@club_router.post("/create")
async def create_club(info: NewClub):
    if not club_service.create_club(info):
        raise HTTPException(status_code=400, detail="Error while creating new club")
    return {"message": "Club created successfully"}

@club_router.put("/update")
async def update_club(info: UpdateClub,
                      token: dict = Depends(get_token_club)):
    if validate_founder_role(token.get("role")):
        club_service.update_club(info, token.get("club"))
        return {"message": "Club updated successfully"}
    else:
        raise HTTPException(status_code=401, detail="You are not authorized to update this club")

@club_router.put("/delete/")
async def delete_club(token: dict = Depends(get_token_club)):
    if validate_founder_role(token.get("role")):
        club_service.delete_club(token.get("club"))
        return {"message": "Club deleted successfully"}
    else:
        raise HTTPException(status_code=401, detail="You are not authorized to delete this club")

@club_router.get("/get/{club_id}")
async def get_club(club_id: str):
    club = club_service.get_club(club_id)
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")
    return club

@club_router.get("/get/all/{user_id}")
async def get_all_clubs(user_id: int):
    return club_service.get_all_clubs(user_id)

@club_router.get("/get/founded/{user_id}", summary="List clubs where the user is the founder")
async def get_founded_clubs(user_id: int):
    return club_service.get_founded_clubs(user_id)

@club_router.get("/get/joined/{user_id}", summary="List clubs where the user is a member")
async def get_joined_clubs(user_id: int):
    return club_service.get_joined_clubs(user_id)


#traer los clubes en los que fuí rechazado o en los que solicité membresía
@club_router.get("/get/requests/id/{user_id}")
async def get_requests(user_id: int):
    return club_service.get_requests(user_id)

@club_router.post("/add/member")
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
    if validate_founder_role(token.get("role")):
        club_service.approve_membership(token.get("club"), membership.id_user)
        return {"message": "Membership approved successfully"}
    else:
        raise HTTPException(status_code=401, detail="You are not authorized to approve membership")


@club_router.patch("/membership/reject")
async def reject_membership(membership: UserID, token: dict = Depends(get_token_club)):
    if validate_founder_role(token.get("role")):
        club_service.reject_membership(token.get("club"), membership.id_user)
        return {"message": "Membership rejected successfully"}
    else:
        raise HTTPException(status_code=401, detail="You are not authorized to reject membership")


@club_router.get("/get/requests/all")
async def get_all_membership_requests(token: dict = Depends(get_token_club)):
    if validate_founder_role(token.get("role")):
        return club_service.get_club_requests(token.get("club"))
    else:
        raise HTTPException(status_code=401, detail="You are not authorized to view membership requests")

@club_router.patch("/membership/remove")
async def remove_member(membership: UserID, token: dict = Depends(get_token_club)):
    if validate_founder_role(token.get("role")):
        club_service.remove_member(token.get("club"), membership.id_user)
        return {"message": "Member removed successfully"}
    else:
        raise HTTPException(status_code=401, detail="You are not authorized to remove this member")


@club_router.post("/add/resource")
async def upload_resource(title: str = Form(...),
                          author: str = Form(...),
                          biblio_ref: str = Form(...),
                          reading_res_desc: str = Form(...),
                          file: UploadFile = File(...),
                          token: dict = Depends(get_token_club)):
    if validate_founder_role(token.get("role")):
        info = ResourceToUpload(title=title,
                                author=author,
                                biblio_ref=biblio_ref,
                                reading_res_desc=reading_res_desc)

        resource_service.upload_resource(info, token.get("club"),file)
        return {"message": "Resource uploaded successfully"}
    else:
        raise HTTPException(status_code=400, detail="You are not authorized to upload a resource")

@club_router.get("/get/resources/id/{resource_id}")
async def get_resource(resource_id: int, token: dict = Depends(get_token_club)):
    return resource_service.get_resource_url(resource_id)

@club_router.patch("/delete/resources/{resource_id}")
async def delete_resource(resource_id: int, token: dict = Depends(get_token_club)):
    if validate_founder_role(token.get("role")):
        resource_service.delete_resource(resource_id)
        return {"message": "Resource deleted successfully"}
    else:
        raise HTTPException(status_code=401, detail="You are not authorized to delete this resource")

@club_router.get("/get/resources/all")
async def get_all_resources_by_club(token: dict = Depends(get_token_club)):
    return resource_service.get_all_resources_by_club(token.get("club"))

@club_router.get("/get/resources/quiz/{resource_id}")
async def get_quiz(resource_id: int, token: dict = Depends(get_token_club)):
    if validate_founder_role(token.get("role")):
        return quiz_service.get_quiz(resource_id)
    if token.get("role") == "Member":
        return quiz_service.get_quiz_member(resource_id)
    else:
        raise HTTPException(status_code=400, detail="Quiz does not exist or you are not authorized to view it")


@club_router.put("/regenerate/resources/quiz/{resource_id}")
async def regenerate_quiz(resource_id: int, token: dict = Depends(get_token_club)):
    if not validate_founder_role(token.get("role")):
        raise HTTPException(status_code=401, detail="You are not authorized to update this quiz")
    return quiz_service.regen_quiz(resource_id)

@club_router.get("/ranking")
async def get_ranking(token: dict = Depends(get_token_club)):
    print(token.get("club"))
    return club_service.get_club_ranking(token.get("club"))

@club_router.get("/get/resources/ranking/{resource_id}")
async def get_ranking_by_resource(resource_id: int, token: dict = Depends(get_token_club)):
    return resource_service.get_ranking_by_resource(resource_id)

#Soon........
@club_router.put("/membership/leave")
async def leave_club():
    if not club_service.leave_club:
        raise HTTPException(status_code=400, detail="Error while leaving club")
    return {"message": "Left club successfully"}




