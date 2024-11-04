from typing import Optional
from fastapi import HTTPException, Depends
from sqlalchemy import and_
from sqlalchemy.orm import Session
from core.database import get_table, get_db
from models.responses import NewClub


class ClubRepository:
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db
        self.clubs_table = get_table('clubs')  # Obtiene la tabla de usuarios
        self.participants_table = get_table('participant_role_club')  # Obtiene la tabla de participantes de un club

    def _get_db(self) -> Session:
        db = next(get_db())  # Obtiene la sesión usando el generador
        return db

    def create_club(self, newclub: NewClub, club_code: str):
        db = self._get_db()
        try:
            query = self.clubs_table.insert().values(
                club_code=club_code,
                club_name=newclub.club_name,
                club_desc=newclub.club_desc,
                is_private=newclub.is_private,
                is_academic=newclub.is_academic
            )
            result = db.execute(query)
            db.commit()
            id_club = result.lastrowid
            print(id_club)
            print(newclub.id_user, newclub.club_name, newclub.club_desc, newclub.is_private, newclub.is_academic, club_code)
            self.add_founder_to_club(id_club, newclub.id_user)
            return True
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"DB Error while creating new club: {e}")
        finally:
            db.close()

    def add_founder_to_club(self, id_club: int, id_user: int):
        db = self._get_db()
        try:
            query = self.participants_table.insert().values(
                id_user=id_user,
                id_role=1,
                id_club=id_club
            )
            db.execute(query)
            db.commit()
            return True
        except Exception:
            db.rollback()
            raise HTTPException(status_code=400, detail="DB Error while adding founder to club")
        finally:
            db.close()

    def get_club(self, club_id: int):
        db = self._get_db()
        try:
            query = self.clubs_table.select().where(self.clubs_table.c.club_id == club_id)
            result = db.execute(query)
            club = result.fetchone()
            return club
        except Exception:
            raise HTTPException(status_code=500, detail="DB Error while getting club")
        finally:
            db.close()

    def is_unique_club_code(self, club_code: str):
        db = self._get_db()
        try:
            query = self.clubs_table.select().where(self.clubs_table.c.club_code == club_code)
            result = db.execute(query)
            club = result.fetchone()
            return club is None
        except Exception:
            raise HTTPException(status_code=500, detail="DB Error while checking club code")
        finally:
            db.close()


