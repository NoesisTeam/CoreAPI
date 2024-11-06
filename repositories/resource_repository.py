from fastapi import HTTPException, Depends
from sqlalchemy import and_
from sqlalchemy.orm import Session
from core.database import get_table, get_db
from models.responses import Resource, ResourceDB


class ResourceRepository:
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db
        self.resources = get_table('reading_resources')

    def _get_db(self) -> Session:
        db = next(get_db())
        return db

    #traer la url del recurso en la tabla reading_resources que tiene ese id
    def get_resource(self, resource_id: int) -> str:
        db = self._get_db()
        try:
            query = self.resources.select(self.resources.c.url_resource).where(self.resources.c.id_reading_resource == resource_id)
            result = db.execute(query)
            resource = result.fetchone()
            if resource is None:
                raise HTTPException(status_code=404, detail="Resource not found")
            return str(resource[0])
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"DB Error while getting url_resource: {e}")
        finally:
            db.close()

    def create_resource(self, info: Resource, url: str):
        db = self._get_db()
        try:
            query = self.resources.insert().values(
                title=info.title,
                author=info.author,
                biblio_ref=info.biblio_ref,
                reading_res_desc = info.reading_res_desc,
                id_club=info.id_club,
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

    def get_resources_by_club(self, club_id: int):
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
