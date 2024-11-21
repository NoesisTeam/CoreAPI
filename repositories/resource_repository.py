from fastapi import HTTPException, Depends
from sqlalchemy import and_
from sqlalchemy.orm import Session
from core.database import get_table, get_db
from models.responses import ResourceToUpload, ResourceDB, ResourceResponse, QuizResult, Ranking


class ResourceRepository:
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db
        self.resources = get_table('reading_resources')
        self.quiz_results = get_table('quiz_results')
        self.quizzes = get_table('quizzez')
        self.participants_table = get_table('participant_role_club')
        self.users = get_table('users')

    def _get_db(self) -> Session:
        db = next(get_db())
        return db

    #traer la url del recurso en la tabla reading_resources que tiene ese id
    def get_resource_url(self, resource_id: int) -> str:
        db = self._get_db()
        try:
            query = self.resources.select().where(self.resources.c.id_reading_resource == resource_id)
            result = db.execute(query)
            resource = result.fetchone()
            if resource is None:
                raise HTTPException(status_code=404, detail="Resource not found")
            return resource.url_resource
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"DB Error while getting url_resource: {e}")
        finally:
            db.close()

    def create_resource(self, info: ResourceToUpload, id_club: int, url: str):
        db = self._get_db()
        try:
            query = self.resources.insert().values(
                title=info.title,
                author=info.author,
                biblio_ref=info.biblio_ref,
                reading_res_desc = info.reading_res_desc,
                id_club=id_club,
                url_resource=url
            )
            db.execute(query)
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"DB Error while creating resource: {e}")
        finally:
            db.close()

    def delete_resource(self, resource_id: int):
        db = self._get_db()
        try:
            query = self.resources.update().where(self.resources.c.id_reading_resource == resource_id).values(
                resource_status = 'I'
            )
            db.execute(query)
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"DB Error while deleting resource: {e}")
        finally:
            db.close()

    def get_all_resources_by_club(self, club_id: int):
        db = self._get_db()
        try:
            query = self.resources.select().where(and_(self.resources.c.id_club == club_id, self.resources.c.resource_status == 'A'))
            result = db.execute(query)
            resources = result.fetchall()
            res_ids = [row.id_reading_resource for row in resources]
            return self.get_resources_by_ids(db, res_ids)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"DB Error while getting resources by club: {e}")
        finally:
            db.close()

    def get_resource_by_id(self, resource_id: int):
        db = self._get_db()
        try:
            query = self.resources.select().where(self.resources.c.id_reading_resource == resource_id)
            result = db.execute(query)
            resource = result.fetchone()
            if resource is None:
                raise HTTPException(status_code=404, detail="Resource not found")
            return ResourceDB(**resource._asdict())
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"DB Error while getting resource by id: {e}")
        finally:
            db.close()

    def get_resource_ranking(self, id_resource: int):
        db = self._get_db()
        try:
            # Join con usuarios y quizzes para obtener los detalles necesarios
            query = self.quiz_results.join(
                self.participants_table,  # Join con la tabla PARTICIPANT_ROLE_CLUB
                and_(
                    self.quiz_results.c.id_user == self.participants_table.c.id_user,
                    self.quiz_results.c.id_role == self.participants_table.c.id_role,
                    self.quiz_results.c.id_club == self.participants_table.c.id_club
                )
            ).join(
                self.users,  # Join con la tabla de usuarios para obtener el nombre del usuario
                self.participants_table.c.id_user == self.users.c.id_user
            ).join(
                self.quizzes,  # Join con la tabla de quizzes para asociar el quiz al recurso de lectura
                self.quiz_results.c.id_quiz == self.quizzes.c.id_quiz
            ).select().where(
                and_(
                    self.quizzes.c.id_reading_resource == id_resource,  # Solo los quizzes asociados al recurso
                    self.participants_table.c.participant_status == 'A'  # Solo participantes activos
                )
            ).order_by(self.quiz_results.c.score.desc())  # Ordenar por el puntaje del quiz

            result = db.execute(query)
            quiz_results = result.fetchall()
            return [Ranking(**quiz._asdict()) for quiz in quiz_results]
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"DB Error while getting resource ranking: {e}")
        finally:
            db.close()

    # Método para obtener recursos por una lista de IDs
    def get_resources_by_ids(self, db, res_ids):
        if res_ids:
            query_res = self.resources.select().where(
                self.resources.c.id_reading_resource.in_(res_ids)
            )
            result_res = db.execute(query_res)
            resources = result_res.fetchall()
            # Convertir cada fila a un objeto ResourceDB
            return [ResourceDB(**resource._asdict()) for resource in resources]
        else:
            return []
