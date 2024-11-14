from fastapi import Depends, HTTPException, status
import random
import string

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError

from core import app_settings
from models.responses import NewClub, UpdateClub
from repositories.club_repository import ClubRepository

settings = app_settings.get_settings()

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="access_token")
# def get_token_club(token: str = Depends(oauth2_scheme)) -> str:
#     credentials_exception = HTTPException(
#         status_code=status.HTTP_401_UNAUTHORIZED,
#         detail="Wrong credentials, not authorized",
#         headers={"WWW-Authenticate": "Bearer"},
#     )
#     try:
#         payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
#         role_name: str = payload.get("role")
#         if role_name is None:
#             raise credentials_exception
#     except JWTError:
#         raise credentials_exception
#     return role_name
def get_token_club(token: str = Depends(oauth2_scheme)) -> dict:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Wrong credentials, not authorized",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("user")
        role_name: str = payload.get("role")
        club_id: int = payload.get("club")
        if user_id is None or role_name is None or club_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    return {"user": user_id, "role": role_name, "club": club_id}

def generate_club_code(is_private: bool, is_academic: bool) -> str:
    if is_private:
        if is_academic:
            prefix = "PRA"
        else:
            prefix = "PRF"
    else:
        if is_academic:
            prefix = "PUA"
        else:
            prefix = "PUF"

    suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
    return prefix + suffix

class ClubService:
    def __init__(self):
        self.repository = ClubRepository()

    def create_club(self, newclub :NewClub):
        club_code = generate_club_code(newclub.is_private, newclub.is_academic)
        while not self.repository.is_unique_club_code(club_code):
            club_code = generate_club_code(newclub.is_private, newclub.is_academic)
        return self.repository.create_club(newclub, club_code)

    def update_club(self, updateclub: UpdateClub, club_id: int):
        return self.repository.update_club(updateclub, club_id)

    def delete_club(self, club_id: int):
        return self.repository.delete_club(club_id)

    def get_club(self, club_id: str):
        return self.repository.get_club(club_id)

    def get_founded_clubs(self, user_id: int):
        return self.repository.get_founded_clubs(user_id)

    def get_joined_clubs(self, user_id: int):
        return self.repository.get_joined_clubs(user_id)

    def request_membership(self, club_id: int, user_id: int):
        return self.repository.request_membership(club_id, user_id)

    def get_requests(self, user_id: int):
        return self.repository.get_requests(user_id)

    def add_member(self, club_id: int, user_id: int):
        return self.repository.add_member(club_id, user_id)

    def approve_membership(self, club_id: int, user_id: int):
        return self.repository.approve_membership(club_id, user_id)

    def reject_membership(self, club_id: int, user_id: int):
        return self.repository.reject_membership(club_id, user_id)

    def get_club_requests(self, club_id: int):
        return self.repository.get_club_requests(club_id)

    def remove_member(self, club_id: int, user_id: int):
        return self.repository.remove_member(club_id, user_id)

    def get_club_ranking(self, club_id: int):
        return self.repository.get_club_ranking(club_id)

    def get_club_by_code(self, club_code: str):
        return self.repository.get_club(club_code)

    def get_all_clubs(self, user_id: int):
        return self.repository.get_all_clubs(user_id)