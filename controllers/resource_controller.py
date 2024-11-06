from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from models.responses import Resource
from services.club_service import validate_role
from services.resource_service import ResourceService

resource_router = APIRouter(prefix="/resource", tags=["Resources"])
resource_service = ResourceService()

def validate_role_in_club(tk_info: str, club_id: int):
    tk_role_name = tk_info.split(":::")[0]
    tk_club_id = int(tk_info.split(":::")[1])
    if tk_role_name == "Founder" and tk_club_id == club_id:
        return True
    else:
        return False
@resource_router.get("/get/{resource_id}")
async def get_resource(resource_id: int):
    return {"message": "Resource retrieved successfully"}

@resource_router.post("/upload")
async def upload_resource(info: Resource,file: UploadFile = File(...), tk_info: str = Depends(validate_role)):
    if validate_role_in_club(tk_info, info.club_id):
        resource_service.upload_resource(info, file)
        return {"message": "Club updated successfully"}
    else:
        raise HTTPException(status_code=400, detail="You are not authorized to upload a resource")