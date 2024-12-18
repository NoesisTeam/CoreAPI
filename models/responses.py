from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, Boolean, DECIMAL, Float
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

class ResourceToUpload(BaseModel):
    title: str
    author : str
    biblio_ref : str
    reading_res_desc : str

class ResourceResponse(BaseModel):
    id_reading_resource: int
    title: str
    author : str
    biblio_ref : str
    reading_res_desc : str
    created_at : str
    url_resource : str

class NewParticipant(BaseModel):
    id_user: int
    id_club: int

class UserID(BaseModel):
    id_user: int

class ClubRequest(Base):
    __tablename__ = "club_requests"

    id_club = Column(Integer, primary_key=True)
    id_user = Column(Integer, primary_key=True)
    id_request_status = Column(Integer)
    request_date = Column(String(50))

class ClubRequestResponse(BaseModel):
    id_club: int
    user_name: str
    id_request_status: int
    request_date: str

class ProfileInfoUp(BaseModel):
    id_user: int
    real_name: str
    phone_number: str
    semester: int
    id_career: int
    sex: str

class ProfileInfo(BaseModel):
    user_name: str
    real_name: Optional[str]
    phone_number: Optional[str]
    semester: Optional[int]
    career_name: Optional[str]
    sex: Optional[str]
    global_score: Decimal

class Career(BaseModel):
    id_career: int
    career_name: str

class ClubParticipant(Base):
    __tablename__ = "club_participants"

    id_club = Column(Integer, primary_key=True)
    id_user = Column(Integer, primary_key=True)
    id_role = Column(Integer)
    quantity_quizzes_solved = Column(Integer)
    quantity_questions_answered = Column(Integer)
    quantity_perfect_quizzes = Column(Integer)
    quantity_reading_resources_read = Column(Integer)
    created_at = Column(String(50))
    nickname = Column(String(50))
    total_score = Column(DECIMAL(10,3))
    participant_status = Column(String(1))

class QuizSubmit(BaseModel):
    id_quiz: int
    answers: List[str]
    time_spent: int

class QuizCompare(BaseModel):
    correct_answers: List[str]
    minutes_to_answer: int
    quantity_questions: int

class QuizResponse(BaseModel):
    correct_answers: List[str]
    score: float
    quantity_correct_answers: int


class ResourceDB(Base):
    __tablename__ = "reading_resources"

    title = Column(String(100))
    author = Column(String(100))
    biblio_ref = Column(String(100))
    reading_res_desc = Column(String(255))
    created_at = Column(String(50))
    url_resource = Column(String(255))
    id_club = Column(Integer)
    id_reading_resource = Column(Integer, primary_key=True, index=True)
    resource_status = Column(String(1))

class QuizMember(BaseModel):
    id_quiz: int
    questions: str
    answers: str
    quantity_questions: int
    minutes_to_answer: int
    id_reading_resource: int

class QuizDB(Base):
    __tablename__ = "quizzez"

    id_quiz = Column(Integer, primary_key=True)
    questions = Column(String(255))
    answers = Column(String(255))
    correct_answers = Column(String(255))
    quantity_questions = Column(Integer)
    minutes_to_answer = Column(Integer)
    id_reading_resource = Column(Integer)

class ClubRanking(BaseModel):
    id_user: int
    user_name: str
    total_score: float

class ResourceRanking(BaseModel):
    id_user: int
    user_name: str
    score: float

class MedalsByClub(BaseModel):
    medal_type_name: str
    medal_q_name: str

class MedalsByUser(BaseModel):
    medal_type_name: str
    medal_q_name: str
    quantity: int

class QuizResult(Base):
    __tablename__ = "quiz_results"

    id_user = Column(Integer, primary_key=True)
    id_role = Column(Integer, primary_key=True)
    id_club = Column(Integer, primary_key=True)
    quantity_correct_answers = Column(Integer)
    time_spent = Column(Integer)
    created_at = Column(String(50))
    score = Column(Float)
    id_quiz = Column(Integer, primary_key=True)