from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from core.database import get_db, get_table
from models.responses import QuizDB


class QuizRepository:
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db
        self.quizzez = get_table('quizzez')
        self.reading_resources = get_table('reading_resources')

    def _get_db(self) -> Session:
        db = next(get_db())
        return db

    def get_quiz(self, quiz_id: int):
        db = self._get_db()
        try:
            query = self.quizzez.select().where(self.quizzez.c.id_quiz == quiz_id)
            result = db.execute(query)
            quiz = result.fetchone()
            if quiz is None:
                raise HTTPException(status_code=404, detail="Quiz not found")
            return QuizDB(**quiz.as_dict())
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"DB Error while getting quiz: {e}")
        finally:
            db.close()

    def add_quiz(self, resource_id: int, quiz: dict):
        db = self._get_db()
        try:
            query = self.quizzez.insert().values(
                questions=quiz.get('questions'),
                answers=quiz.get('answers'),
                correct_answers=quiz.get('correct_answers'),
                quantity_questions=quiz.get('quantity_questions'),
                minutes_to_answer=quiz.get('minutes_to_answer'),
                id_reading_resource=resource_id
            )
            db.execute(query)
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"DB Error while adding quiz: {e}")
        finally:
            db.close()

    def update_quiz(self, quiz_id: int, quiz: dict):
        db = self._get_db()
        try:
            query = self.quizzez.update().where(self.quizzez.c.id_quiz == quiz_id).values(
                questions=quiz.get('questions'),
                answers=quiz.get('answers'),
                correct_answers=quiz.get('correct_answers'),
                quantity_questions=quiz.get('quantity_questions'),
                minutes_to_answer=quiz.get('minutes_to_answer'),
            )
            db.execute(query)
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"DB Error while updating quiz: {e}")
        finally:
            db.close()

    def quiz_exists(self, resource_id: int):
        db = self._get_db()
        try:
            query = self.quizzez.select().where(self.quizzez.c.id_reading_resource == resource_id)
            result = db.execute(query)
            quiz = result.fetchone()
            if quiz is None:
                return False
            return True
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"DB Error while getting quiz: {e}")
        finally:
            db.close()

