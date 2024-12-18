from typing import Optional
from fastapi import HTTPException, Depends
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session
from sqlalchemy.sql.functions import count
from starlette.responses import JSONResponse

from core.database import get_table, get_db
from models.responses import NewClub, UpdateClub, Club, ClubRequest, ClubParticipant, ClubRanking, MedalsByUser, \
    MedalsByClub, ProfileInfoUp, ProfileInfo, Career


class ClubRepository:
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db
        self.clubs_table = get_table('clubs')  # Obtiene la tabla de usuarios
        self.participants_table = get_table('participant_role_club')  # Obtiene la tabla de participantes de un club
        self.club_requests_table = get_table('club_requests')  # Obtiene la tabla de solicitudes de membresía
        self.users_table = get_table('users')  # Obtiene la tabla de usuarios
        self.medals_awarded = get_table('medals_awarded')  # Obtiene la tabla de medallas otorgadas
        self.medal_qualities = get_table('medal_qualities')  # Obtiene la tabla de calidades de medallas
        self.medal_types = get_table('medal_types')  # Obtiene la tabla de tipos de medallas
        self.careers = get_table('careers')  # Obtiene la tabla de carreras

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

    # Método para obtener todos los clubes activos en los que no soy fundador ni miembro y tampoco he solicitado membresía
    def get_all_clubs(self, id_user: int):
        db = self._get_db()
        try:
            query = self.clubs_table.select().where(
                and_(
                    ~self.clubs_table.c.id_club.in_(
                        self.participants_table.select().where(
                            self.participants_table.c.id_user == id_user
                        ).with_only_columns(self.participants_table.c.id_club)
                    ),
                    ~self.clubs_table.c.id_club.in_(
                        self.club_requests_table.select().where(
                            self.club_requests_table.c.id_user == id_user
                        ).with_only_columns(self.club_requests_table.c.id_club)
                    ),
                    self.clubs_table.c.club_status == 'A'
                )
            )
            result = db.execute(query)
            clubs = result.fetchall()
            return [Club(**club._asdict()) for club in clubs]  # Convertir cada fila a un objeto Club
        except Exception as e:
            raise HTTPException(status_code=500, detail="DB Error while getting all clubs " + str(e))
        finally:
            db.close()

    # Método para obtener todos los clubes creados por un usuario (role=Founder)
    def get_founded_clubs(self, id_user: int):
        db = self._get_db()
        try:
            query = self.participants_table.join(
                self.clubs_table,
                self.participants_table.c.id_club == self.clubs_table.c.id_club
            ).select().where(
                and_(
                    self.participants_table.c.id_user == id_user,
                    self.participants_table.c.id_role == 1,
                    self.clubs_table.c.club_status == 'A'
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
            query = self.participants_table.join(
                self.clubs_table,
                self.participants_table.c.id_club == self.clubs_table.c.id_club
            ).select().where(
                and_(
                    self.participants_table.c.id_user == id_user,
                    self.participants_table.c.id_role == 2,
                    self.clubs_table.c.club_status == 'A'
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

    def get_club(self, club_id: str):
        db = self._get_db()
        try:
            query = self.clubs_table.select().where(
                and_(
                    or_(self.clubs_table.c.id_club == club_id,
                        self.clubs_table.c.club_code== club_id
                        ),
                        self.clubs_table.c.club_status == 'A'))
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
            #retornar el objeto creado
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

    def get_requests(self, user_id: int):
        db = self._get_db()
        try:
            query = self.club_requests_table.select().where(and_(self.club_requests_table.c.id_user == user_id,
                                                                 self.club_requests_table.c.id_request_status != 1))
            result = db.execute(query)
            requests = result.fetchall()
            return [ClubRequest(**request._asdict()) for request in requests]
        except Exception:
            raise HTTPException(status_code=500, detail="DB Error while getting requests")
        finally:
            db.close()

    def get_club_requests_with_user_names(self, club_id: int):
        db = self._get_db()
        try:
            # Realizamos un JOIN entre club_requests_table y users_table para obtener solo los campos necesarios
            query = self.club_requests_table.join(
                self.users_table,
                self.club_requests_table.c.id_user == self.users_table.c.id_user
            ).select().where(
                and_(
                    self.club_requests_table.c.id_club == club_id,
                    self.club_requests_table.c.id_request_status == 2
                )
            )

            result = db.execute(query)
            requests = result.fetchall()

            # Filtramos los datos para solo incluir los campos requeridos en la respuesta
            return [
                {
                    "id_club": request.id_club,
                    "id_user": request.id_user,
                    "request_date": request.request_date,
                    "user_name": request.user_name
                }
                for request in requests
            ]
        except Exception:
            raise HTTPException(status_code=500, detail="DB Error while getting club requests with user names")
        finally:
            db.close()

    def approve_membership(self, club_id: int, user_id: int):
        db = self._get_db()
        try:
            query = self.club_requests_table.update().where(
                and_(
                    self.club_requests_table.c.id_club == club_id,
                    self.club_requests_table.c.id_user == user_id,
                    self.club_requests_table.c.id_request_status == 2
                )
            ).values(
                id_request_status=1
            )
            result = db.execute(query)
            if result.rowcount == 0:  # rowcount indica el número de filas afectadas
                raise HTTPException(status_code=404, detail="Request is not pending")
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
                    self.club_requests_table.c.id_user == user_id,
                    self.club_requests_table.c.id_request_status == 2
                )
            ).values(
                id_request_status=3
            )
            result = db.execute(query)
            if result.rowcount == 0:  # rowcount indica el número de filas afectadas
                raise HTTPException(status_code=404, detail="Request is not pending")
            db.commit()
            return True
        except Exception:
            db.rollback()
            raise HTTPException(status_code=400, detail="DB Error while rejecting membership")
        finally:
            db.close()

    # Método para obtener el ranking de un club ordenado de mayor a menor segun la columna total_score
    def get_club_ranking(self, club_id: int):
        db = self._get_db()
        try:
            #join con users para obtener el nombre del usuario
            query = self.participants_table.join(
                self.users_table,
                self.participants_table.c.id_user == self.users_table.c.id_user
            ).select().where(
                and_(
                    self.participants_table.c.id_club == club_id,
                    self.participants_table.c.participant_status == 'A'
                )
            ).order_by(self.participants_table.c.total_score.desc())
            result = db.execute(query)
            participants = result.fetchall()
            return [ClubRanking(**participant._asdict()) for participant in participants]
        except Exception as e:
            raise HTTPException(status_code=500, detail="DB Error while getting club ranking" + str(e))
        finally:
            db.close()

    def get_member_medals_by_club(self, club_id: int, user_id: int):
        db = self._get_db()
        try:
            query = self.medals_awarded.join(
                self.medal_qualities,
                self.medals_awarded.c.id_medal_quality == self.medal_qualities.c.id_medal_quality
            ).join(
                self.medal_types,
                self.medal_qualities.c.id_medal_type == self.medal_types.c.id_medal_type
            ).select().with_only_columns(
                self.medal_qualities.c.medal_q_name,
                self.medal_types.c.medal_type_name
            ).where(
                and_(
                    self.medals_awarded.c.id_club == club_id,
                    self.medals_awarded.c.id_user == user_id
                )
            )
            result = db.execute(query)
            medals = result.fetchall()
            print(medals)
            return [MedalsByClub(**medal._asdict()) for medal in medals]
        except Exception as e:
            raise HTTPException(status_code=500, detail="DB Error while getting member medals by club" + str(e))
        finally:
            db.close()

    def get_user_medals(self, id_user: int):
        db = self._get_db()
        try:
            query = self.medals_awarded.join(
                self.medal_qualities,
                self.medals_awarded.c.id_medal_quality == self.medal_qualities.c.id_medal_quality
            ).join(
                self.medal_types,
                self.medal_qualities.c.id_medal_type == self.medal_types.c.id_medal_type
            ).select().with_only_columns(
                self.medal_qualities.c.medal_q_name,
                self.medal_types.c.medal_type_name,
                count(self.medals_awarded.c.id_medal_quality).label('quantity')
            ).where(
                self.medals_awarded.c.id_user == id_user
            ).group_by(
                self.medals_awarded.c.id_medal_quality
            )
            result = db.execute(query)
            medals = result.fetchall()
            return [MedalsByUser(**medal._asdict()) for medal in medals]
        except Exception as e:
            raise HTTPException(status_code=500, detail="DB Error while getting user medals" + str(e))
        finally:
            db.close()

    #traer la info del usuario haciendo join con careers para obtener el career_name
    def get_user_profile(self, user_id: int):
        print(user_id)
        db = self._get_db()
        try:
            # Usar un LEFT JOIN para manejar usuarios sin carrera
            query = self.users_table.join(
                self.careers,
                self.users_table.c.id_career == self.careers.c.id_career,
                isouter=True  # Esto realiza un LEFT JOIN
            ).select().where(self.users_table.c.id_user == user_id)

            result = db.execute(query)
            user = result.fetchone()

            if user is None:
                raise HTTPException(status_code=404, detail="User not found")

            # Convertir el resultado a un dict y manejar valores nulos en `career_name`
            user_data = user._asdict()
            user_data["career_name"] = user_data.get("career_name") or None  # Asegura que sea None si es NULL

            return ProfileInfo(**user_data)
        except Exception as e:
            raise HTTPException(status_code=400, detail="DB Error while getting user profile: " + str(e))
        finally:
            db.close()

    def update_user_profile(self, info: ProfileInfoUp):
        db = self._get_db()
        try:
            query = self.users_table.update().where(self.users_table.c.id_user == info.id_user).values(
                real_name=info.real_name,
                phone_number=info.phone_number,
                semester=info.semester,
                id_career=info.id_career,
                sex= info.sex
            )
            result = db.execute(query)
            if result.rowcount == 0:  # rowcount indica el número de filas afectadas
                raise HTTPException(status_code=404, detail="User not found")
            db.commit()

            return "User profile updated"
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=400, detail="DB Error while updating user profile" + str(e))
        finally:
            db.close()
    # verificar si el usuario ya tiene completos los campos de real_name, phone_number, semester, career
    def check_user_info(self, user_id: int):
        db = self._get_db()
        try:
            query = self.users_table.select().where(self.users_table.c.id_user == user_id)
            result = db.execute(query)
            user = result.fetchone()
            if user is None:
                raise HTTPException(status_code=404, detail="User not found")
            if user.real_name is None or user.phone_number is None or user.semester is None or user.id_career is None or user.sex is None:
                return JSONResponse(status_code=200, content={"complete": False})
            return JSONResponse(status_code=200, content={"complete": True})
        except Exception as e:
            raise HTTPException(status_code=400, detail="DB Error while checking user info" + str(e))
        finally:
            db.close()

    def get_all_careers(self):
        db = self._get_db()
        try:
            query = self.careers.select()
            result = db.execute(query)
            careers = result.fetchall()
            return [Career(**career._asdict()) for career in careers]
        except Exception as e:
            raise HTTPException(status_code=400, detail="DB Error while getting all careers" + str(e))
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
