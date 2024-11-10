from typing import Optional
from fastapi import HTTPException, Depends
from sqlalchemy import and_
from sqlalchemy.orm import Session
from core.database import get_table, get_db
from models.responses import NewClub, UpdateClub, Club, ClubRequest


class ClubRepository:
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db
        self.clubs_table = get_table('clubs')  # Obtiene la tabla de usuarios
        self.participants_table = get_table('participant_role_club')  # Obtiene la tabla de participantes de un club
        self.club_requests_table = get_table('club_requests')  # Obtiene la tabla de solicitudes de membresía

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

    def update_club(self,updateclub: UpdateClub, club_id: int):
        db = self._get_db()
        try:
            query = self.clubs_table.update().where(self.clubs_table.c.id_club == club_id).values(
                club_name=updateclub.club_name,
                club_desc=updateclub.club_desc,
                is_private=updateclub.is_private,
                is_academic=updateclub.is_academic
            )
            db.execute(query)
            db.commit()
            return True
        except Exception:
            db.rollback()
            raise HTTPException(status_code=400, detail="DB Error while updating club")
        finally:
            db.close()

    def delete_club(self, club_id: int):
        db = self._get_db()
        try:
            query = self.clubs_table.update().where(self.clubs_table.c.id_club == club_id).values(
                club_status='I'
            )
            db.execute(query)
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=400, detail="DB Error while deleting club" + str(e))
        finally:
            db.close()

    def all_clubs(self):
        db = self._get_db()
        try:
            query = self.clubs_table.select()
            result = db.execute(query)
            clubs = result.fetchall()
            return [Club(**club._asdict()) for club in clubs]
        except Exception as e:
            raise HTTPException(status_code=500, detail="DB Error while getting all clubs: " + str(e))
        finally:
            db.close()

    # Método para obtener todos los clubes creados por un usuario (role=Founder)
    def get_founded_clubs(self, id_user: int):
        db = self._get_db()
        try:
            query = self.participants_table.select().where(
                and_(
                    self.participants_table.c.id_user == id_user,
                    self.participants_table.c.id_role == 1
                )
            )
            result = db.execute(query)
            club_ids = [row.id_club for row in result.fetchall()]
            return self.get_clubs_by_ids(db, club_ids)
        except Exception:
            raise HTTPException(status_code=500, detail="DB Error while getting clubs by founder")
        finally:
            db.close()

    # Método para obtener todos los clubes en los que participa un usuario (role=Member)
    def get_joined_clubs(self, id_user: int):
        db = self._get_db()
        try:
            query = self.participants_table.select().where(
                and_(
                    self.participants_table.c.id_user == id_user,
                    self.participants_table.c.id_role == 2
                )
            )
            result = db.execute(query)
            clubs = result.fetchall()
            club_ids = [row.id_club for row in clubs]
            return self.get_clubs_by_ids(db, club_ids)
        except Exception:
            raise HTTPException(status_code=500, detail="DB Error while getting clubs by member")
        finally:
            db.close()

    # Método para obtener clubes por una lista de IDs
    def get_clubs_by_ids(self, db, club_ids):
        if club_ids:
            query_clubs = self.clubs_table.select().where(
                self.clubs_table.c.id_club.in_(club_ids)
            )
            result_clubs = db.execute(query_clubs)
            clubs = result_clubs.fetchall()
            return [Club(**club._asdict()) for club in clubs]  # Convertir cada fila a un objeto Club
        else:
            return []

    # Método para agregar al fundador como miembro del club creado
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
            query = self.clubs_table.select().where(and_(self.clubs_table.c.id_club == club_id, self.clubs_table.c.club_status == 'A'))
            result = db.execute(query)
            club = result.fetchone()
            if club is None:
                raise HTTPException(status_code=404, detail="Club not found")
            else:
                return Club(id_club=club.id_club,
                        club_code=club.club_code,
                        club_name=club.club_name,
                        club_desc=club.club_desc,
                        is_private=club.is_private,
                        is_academic=club.is_academic)
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

    def add_member(self, club_id: int, user_id: int):
        db = self._get_db()
        try:
            query = self.participants_table.insert().values(
                id_user=user_id,
                id_role=2,
                id_club=club_id
            )
            db.execute(query)
            db.commit()
            return True
        except Exception:
            db.rollback()
            raise HTTPException(status_code=400, detail="DB Error while adding member to club")
        finally:
            db.close()

    def request_membership(self, club_id: int, user_id: int):
        db = self._get_db()
        try:
            query = self.club_requests_table.insert().values(
                id_club=club_id,
                id_user=user_id,
                id_request_status=2
            )
            db.execute(query)
            db.commit()
            return True
        except Exception:
            db.rollback()
            raise HTTPException(status_code=400, detail="DB Error while requesting membership")
        finally:
            db.close()

    def get_club_requests(self, club_id: int):
        db = self._get_db()
        try:
            query = self.club_requests_table.select().where(
                and_(
                    self.club_requests_table.c.id_club == club_id,
                    self.club_requests_table.c.id_request_status == 2
                )
            )
            result = db.execute(query)
            requests = result.fetchall()
            return [ClubRequest(**request._asdict()) for request in requests]
        except Exception:
            raise HTTPException(status_code=500, detail="DB Error while getting club requests")
        finally:
            db.close()

    def approve_membership(self, club_id: int, user_id: int):
        db = self._get_db()
        try:
            query = self.club_requests_table.update().where(
                and_(
                    self.club_requests_table.c.id_club == club_id,
                    self.club_requests_table.c.id_user == user_id
                )
            ).values(
                id_request_status=1
            )
            db.execute(query)
            db.commit()
            self.add_member(club_id, user_id)
            return True
        except Exception:
            db.rollback()
            raise HTTPException(status_code=400, detail="DB Error while approving membership")
        finally:
            db.close()

    def reject_membership(self, club_id: int, user_id: int):
        db = self._get_db()
        try:
            query = self.club_requests_table.update().where(
                and_(
                    self.club_requests_table.c.id_club == club_id,
                    self.club_requests_table.c.id_user == user_id
                )
            ).values(
                id_request_status=3
            )
            db.execute(query)
            db.commit()
            return True
        except Exception:
            db.rollback()
            raise HTTPException(status_code=400, detail="DB Error while rejecting membership")
        finally:
            db.close()

    def remove_member(self, club_id: int, user_id: int):
        db = self._get_db()
        try:
            query = self.participants_table.update().where(
                and_(
                    self.participants_table.c.id_club == club_id,
                    self.participants_table.c.id_user == user_id
                )
            ).values(
                    participant_status='I'
                )
            db.execute(query)
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=400, detail="DB Error while removing member" + str(e))
        finally:
            db.close()