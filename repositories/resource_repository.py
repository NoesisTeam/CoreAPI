from fastapi import HTTPException, Depends
from sqlalchemy import and_
from sqlalchemy.orm import Session
from core.database import get_table, get_db
from models.responses import ResourceToUpload, ResourceDB, ResourceResponse, QuizResult


class ResourceRepository:
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db
        self.resources = get_table('reading_resources')
        self.quiz_results = get_table('quiz_results')
        self.quizzes = get_table('quizzez')

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

    # Método para obtener el ranking de miembros por recurso de lectura según el score en la tabla quiz_results usando id_resource para buscar el id_quiz de ese recurso en la tabla quizzez y luego buscar el score en la tabla quiz_results usando ese id_quiz
    def get_ranking_by_resource(self, resource_id: int, club_id: int):
        db = self._get_db()
        try:
            query = self.quizzes.select().where(self.quizzes.c.id_reading_resource == resource_id)
            result = db.execute(query)
            quiz = result.fetchone()
            if quiz is None:
                raise HTTPException(status_code=404, detail="Quiz not found")
            else:
                query_res = self.quiz_results.select().where(and_(self.quiz_results.c.id_quiz == quiz.id_quiz,
                                                                  self.quiz_results.c.id_club == club_id)
                                                             ).order_by(self.quiz_results.c.score.desc())
                result_res = db.execute(query_res)
                quiz_results = result_res.fetchall()
                return QuizResult(**quiz_results[0]._asdict())
        except HTTPException as http_exc:
            # Permitir que las excepciones HTTP pasen tal como son (404, etc.)
            raise http_exc
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"DB Error while getting ranking by resource: {e}")
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
