from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
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

class UpdateClub(BaseModel):
    club_name: str
    club_desc : str
    is_private: bool
    is_academic: bool

class Club(Base):
    __tablename__ = "clubs"

    id_club = Column(Integer, primary_key=True, index=True)
    club_code = Column(String(50))
    club_name = Column(String(60))
    club_desc = Column(String(255))
    is_private = Column(Boolean)
    is_academic = Column(Boolean)