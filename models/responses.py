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
    created_at = Column(String(50))
    club_status = Column(String(1))

class Resource(BaseModel):
    id_club: int
    title_resource: str
    author : str
    biblio_ref : str
    reading_res_desc : str

class ResourceDB(Base):
    __tablename__ = "reading_resources"

    title = Column(String(100))
    author = Column(String(100))
    biblio_ref = Column(String(100))
    reading_res_desc = Column(String(255))
    created_at = Column(String(50))
    url_resource = Column(String(255))
    id_club = Column(Integer)
    id_quiz = Column(Integer)
    id_reading_resource = Column(Integer, primary_key=True, index=True)
    resource_status = Column(String(1))