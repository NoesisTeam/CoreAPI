from fastapi import Depends, HTTPException, status
from models.responses import TokenData, NewClub
from repositories.club_repository import ClubRepository
from core import app_settings
from jose import jwt, JWTError
from fastapi.security import OAuth2PasswordBearer
import random
import string

settings = app_settings.get_settings()

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="access_token")
def validate_role(token: str = Depends(oauth2_scheme)):
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
        token_data = TokenData(user_id=user_id, role_name=role_name, club_id=club_id)
    except JWTError:
        raise credentials_exception
    return token_data


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