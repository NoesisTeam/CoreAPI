import json
from itertools import count
from typing import List
from fastapi import Depends, HTTPException
from sqlalchemy import and_
from sqlalchemy.orm import Session


from core.database import get_db, get_table
from models.responses import QuizDB, QuizMember, QuizCompare, QuizResponse


class QuizRepository:
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db
        self.quizzes = get_table('quizzez')
        self.reading_resources = get_table('reading_resources')
        self.quiz_results = get_table('quiz_results')

    def _get_db(self) -> Session:
        db = next(get_db())
        return db

    def get_quiz(self, resource_id: int):
        db = self._get_db()
        print(f"Resource ID: {resource_id}")
        try:
            query = self.quizzes.select().where(self.quizzes.c.id_reading_resource == resource_id)
            result = db.execute(query)
            quiz = result.fetchone()
            if quiz is None:
                raise HTTPException(status_code=404, detail="Quiz not found")
            return QuizDB(**quiz._asdict())
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"DB Error while getting quiz: {e}")
        finally:
            db.close()

    def save_quiz(self, resource_id: int, quiz: dict):
        db = self._get_db()
        print(f"quiz: {quiz}")
        try:
            # Convertir listas a cadenas JSON sin codificación Unicode
            questions_json = json.dumps(quiz.get('questions'), ensure_ascii=False)
            answers_json = json.dumps(quiz.get('options'), ensure_ascii=False)
            correct_answers_json = json.dumps(quiz.get('answers'), ensure_ascii=False)

            query = self.quizzes.insert().values(
                questions=questions_json,
                answers=answers_json,
                correct_answers=correct_answers_json,
                quantity_questions=quiz.get('quantity_questions'),
                minutes_to_answer=quiz.get('quantity_questions'),
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

    def regen_quiz(self, resource_id, quiz: dict):
        id_quiz = self.get_quiz(resource_id).id_quiz
        db = self._get_db()
        try:
            # Convertir listas a cadenas JSON sin codificación Unicode
            questions_json = json.dumps(quiz.get('questions'), ensure_ascii=False)
            answers_json = json.dumps(quiz.get('options'), ensure_ascii=False)
            correct_answers_json = json.dumps(quiz.get('answers'), ensure_ascii=False)

            query = self.quizzes.update().where(and_(self.quizzes.c.id_reading_resource == resource_id,
                                                     self.quizzes.c.id_quiz == id_quiz)).values(
                questions=questions_json,
                answers=answers_json,
                correct_answers=correct_answers_json,
                quantity_questions=quiz.get('quantity_questions'),
                minutes_to_answer=quiz.get('quantity_questions')
            )
            db.execute(query)
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"DB Error while adding quiz: {e}")
        finally:
            db.close()

    def quiz_exists(self, resource_id: int):
        print(resource_id)
        db = self._get_db()
        try:
            query = self.quizzes.select().where(self.quizzes.c.id_reading_resource == resource_id)
            result = db.execute(query)
            quiz = result.fetchone()
            return quiz is not None
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"DB Error while checking quiz existence: {e}")
        finally:
            db.close()

    #trae el quiz de la base de datos asociado al resource_id sin las respuestas correctas
    def get_quiz_from_db_for_members(self, resource_id: int):
        db = self._get_db()
        try:
            query = self.quizzes.select().where(self.quizzes.c.id_reading_resource == resource_id)
            result = db.execute(query)
            quiz = result.fetchone()
            if quiz is None:
                raise HTTPException(status_code=404, detail="Quiz not found")
            return QuizMember(id_quiz=quiz.id_quiz,
                              questions=quiz.questions,
                              answers=quiz.answers,
                              quantity_questions=quiz.quantity_questions,
                              minutes_to_answer=quiz.minutes_to_answer,
                              id_reading_resource=quiz.id_reading_resource)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"DB Error while getting quiz: {e}")
        finally:
            db.close()

    def get_items_quiz(self, id_quiz: int):
        db = self._get_db()
        try:
            query = self.quizzes.select().where(self.quizzes.c.id_quiz == id_quiz)
            result = db.execute(query)
            quiz = result.fetchone()
            if quiz is None:
                raise HTTPException(status_code=404, detail="Quiz not found")
            return QuizCompare(correct_answers=json.loads(quiz.correct_answers),
                                 minutes_to_answer=quiz.minutes_to_answer,
                                 quantity_questions=quiz.quantity_questions)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"DB Error while getting correct answers: {e}")
        finally:
            db.close()
    def is_quiz_answered(self, id_user: int, id_club:int, id_quiz: int):
        db = self._get_db()
        try:
            query = self.quiz_results.select().where(and_(self.quiz_results.c.id_user == id_user,
                                                          self.quiz_results.c.id_club == id_club,
                                                          self.quiz_results.c.id_quiz == id_quiz))
            result = db.execute(query)
            quiz = result.fetchone()
            return quiz is not None
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"DB Error while checking quiz existence: {e}")
        finally:
            db.close()

    def get_quiz_results(self, id_user: int, id_club: int, id_quiz: int, correct_answers: str):
        db = self._get_db()
        try:
            query = self.quiz_results.select().where(and_(self.quiz_results.c.id_user == id_user,
                                                          self.quiz_results.c.id_club == id_club,
                                                          self.quiz_results.c.id_quiz == id_quiz))
            result = db.execute(query)
            quiz = result.fetchone()
            if quiz is None:
                raise HTTPException(status_code=404, detail="Quiz result not found")
            return QuizResponse(correct_answers=correct_answers,
                                score=self.truncate_float(quiz.score, 3),
                                quantity_correct_answers=quiz.quantity_correct_answers)

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"DB Error while getting quiz results: {e}")
        finally:
            db.close()
    def submit_quiz(self, score: float, correct_answers: str ,time_spent: int,answer_correctly: List[bool], id_quiz: int, id_user: int, id_club: int, id_role: int):
        db = self._get_db()
        try:
            query = self.quiz_results.insert().values(
                id_user=id_user,
                id_role=id_role,
                id_club=id_club,
                quantity_correct_answers=answer_correctly.count(True),
                time_spent=time_spent,
                score=score,
                id_quiz=id_quiz
            )
            db.execute(query)
            db.commit()
            return QuizResponse(correct_answers=correct_answers,
                                score=self.truncate_float(score, 3),
                                quantity_correct_answers=answer_correctly.count(True))
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"DB Error while submitting quiz: {e}")
        finally:
            db.close()

    def truncate_float(self, value: float, decimals: int) -> float:
        factor = 10 ** decimals
        return int(value * factor) / factor
