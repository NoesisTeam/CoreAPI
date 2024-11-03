from typing import Optional
from fastapi import HTTPException, Depends
from sqlalchemy import and_
from sqlalchemy.orm import Session
from core.database import get_table, get_db


class ClubRepository:
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db
        self.users_table = get_table('clubs')  # Obtiene la tabla de usuarios

    def _get_db(self) -> Session:
        db = next(get_db())  # Obtiene la sesión usando el generador
        return db

    # def find_by_user_name(self, user_name: str) -> Optional[User]:
    #     db = self._get_db()  # Obtiene la sesión
    #     try:
    #         query = db.query(self.users_table).filter(
    #             and_(self.users_table.c.user_name == user_name)
    #         )
    #         row = query.first()  # Obtiene el primer resultado
    #         if row:
    #             return User(id=row.id_user, user_name=row.user_name, user_password=row.user_password)
    #         return None
    #     finally:
    #         db.close()

