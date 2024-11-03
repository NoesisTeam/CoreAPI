from pydantic import BaseModel

class TokenData(BaseModel):
    user_id: int
    role_name: str
    club_id: int