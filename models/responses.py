from pydantic import BaseModel

class TokenData(BaseModel):
    user_id: int
    role_name: str
    club_id: int

class NewClub(BaseModel):
    id_user: int
    club_name: str
    club_desc : str
    is_private: bool
    is_academic: bool