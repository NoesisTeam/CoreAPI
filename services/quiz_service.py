from typing import List

import requests
from fastapi import HTTPException
from fastapi.responses import JSONResponse

from core.app_settings import get_settings
from models.responses import QuizSubmit
from repositories.quiz_repository import QuizRepository
from services.resource_service import ResourceService

settings = get_settings()

import json
MAX_QUANTITY_QUESTIONS = 5

def process_quiz_data(quiz_json):
    try:
        # Cargar el JSON si es un string
        if isinstance(quiz_json, str):
            quiz = json.loads(quiz_json)
        else:
            quiz = quiz_json

        # Verificar que el formato de quiz es correcto
        if not all(key in quiz for key in ["questions", "options", "answers"]):
            raise ValueError("JSON does not have the required keys")

        # Inicializar estructuras de datos
        questions = []
        all_answers = []
        correct_answers = []

        # Procesar preguntas
        for question_text in quiz["questions"]:
            if not isinstance(question_text, str):
                raise ValueError(f"Questions must be strings. Got: {type(question_text)}")
            # Extraer el texto de la pregunta eliminando el número y el punto
            question_text_only = question_text.split(" ", 1)[1].strip()
            questions.append({"question": question_text_only})

        # Procesar opciones (4 opciones por pregunta)
        options = quiz["options"]
        if len(options) % 4 != 0:
            raise ValueError("Number of options is not multiple of 4")

        for i in range(0, len(options), 4):
            option_set = options[i:i+4]
            # Guardar las opciones agrupadas
            all_answers.append([opt.split("-", 1)[1].strip() for opt in option_set])

        # Procesar respuestas correctas
        correct_answers = quiz["answers"]

        # Verificar consistencia
        if len(questions) != len(all_answers) or len(questions) != len(correct_answers):
            raise ValueError("Quantities of questions, options and answers are not the same.")

        # Estructurar el diccionario final
        processed_quiz = {
            "questions": questions,
            "options": all_answers,
            "answers": correct_answers,
            "quantity_questions": len(questions)
        }
        print(processed_quiz)
        return processed_quiz

    except Exception as e:
        return {"error": str(e)}





class QuizService:
    def __init__(self):
        self.quiz_repository = QuizRepository()
        self.resource_service = ResourceService()

    def get_quiz(self, resource_id: int, id_user: str):
        if self.quiz_repository.quiz_exists(resource_id):
            return self.quiz_repository.get_quiz(resource_id)

        # Si no existe el quiz en la base de datos, se obtiene de la IA_API
        else:
            quiz = self.get_data(resource_id, id_user)
            self.quiz_repository.save_quiz(resource_id, quiz)
            return self.get_quiz_from_db_for_founder(resource_id)

    def get_data(self, resource_id: int, id_user: str):

        try:

            url = settings.AI_API_URL # URL de la API externa
            headers = {
                "Content-Type": "application/json"  # Establece el tipo de contenido a JSON

            }
            data_sent = {
                "resource_url": self.resource_service.get_resource_url(resource_id), # URL del recurso
                "id_user": id_user  # ID del usuario
            }
            response = requests.post(url, headers=headers, json=data_sent)  # Envía el 'data' en formato JSON
            data_quiz = response.json()  # Obtiene el JSON de la respuesta
            print(data_sent)
            # Verifica la respuesta
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code,
                                    detail="Error while getting quiz from AI_API" + str(data_quiz))

            # Verifica que la estructura del JSON sea la esperada
            if not self.is_validate_quiz_response(data_quiz):
                raise HTTPException(status_code=500, detail="IA_API response hasnot valid keys to process it")
            print(data_quiz)
            return process_quiz_data(data_quiz) # Retorna el JSON con la estructura obtenida


        except HTTPException as http_exc:
            raise http_exc

        except Exception as e:
            raise HTTPException(status_code=500, detail="Error while getting quiz from AI_API" + str(e))

    def is_validate_quiz_response(self, data_quiz):
        # Claves requeridas en la respuesta
        required_keys = ["questions", "options", "answers"]
        # Verificar que las claves requeridas estén presentes en la respuesta
        if not all(key in data_quiz for key in required_keys):
            return False

        return True

    def get_quiz_from_db_for_founder(self, resource_id: int):
        if not self.quiz_repository.quiz_exists(resource_id):
            raise HTTPException(status_code=404, detail="Quiz not found")
        return self.quiz_repository.get_quiz(resource_id)

    def get_quiz_from_db_for_members(self, resource_id: int):
        if not self.quiz_repository.quiz_exists(resource_id):
            raise HTTPException(status_code=404, detail="Quiz not found")
        return self.quiz_repository.get_quiz_from_db_for_members(resource_id)

    def regen_quiz(self, resource_id: int, id_user: str):
        quiz = self.get_data(resource_id, id_user)
        self.quiz_repository.regen_quiz(resource_id, quiz)
        return self.get_quiz_from_db_for_founder(resource_id)

    def submit_quiz(self, quiz_submit: QuizSubmit, id_user: int, id_club: int, id_role: int):
        correct_quiz = self.quiz_repository.get_items_quiz(quiz_submit.id_quiz)
        if not self.quiz_repository.is_quiz_answered(id_user, id_club, quiz_submit.id_quiz):
            correct_answers = correct_quiz.correct_answers
            score, answered_correctly = self.calculate_score(quiz_submit, correct_quiz)
            return self.quiz_repository.submit_quiz(score,
                                                    correct_answers,
                                                    quiz_submit.time_spent,
                                                    answered_correctly,
                                                    quiz_submit.id_quiz,
                                                    id_user, id_club, id_role)
        else:
            return self.quiz_repository.get_quiz_results(id_user, id_club, quiz_submit.id_quiz, correct_quiz.correct_answers)

    def check_quiz_answered(self, id_quiz: int, id_club:int, id_user: int):
        return JSONResponse(content={"answered": self.quiz_repository.is_quiz_answered(id_user, id_club, id_quiz)})

    def calculate_score(self, quiz_submit: QuizSubmit, correct_quiz):
        score = 0
        answered_correctly: List[bool] = []
        total_time = correct_quiz.minutes_to_answer * 60
        answer_value = (MAX_QUANTITY_QUESTIONS/correct_quiz.quantity_questions)
        for i in range(correct_quiz.quantity_questions):
            if quiz_submit.answers[i] == correct_quiz.correct_answers[i]:
                answered_correctly.append(True)
                score += answer_value
            else:
                answered_correctly.append(False)
        if quiz_submit.time_spent <= total_time*0.25:
            score *= 1.3
        elif quiz_submit.time_spent <= total_time*0.5:
            score *= 1.2
        elif quiz_submit.time_spent <= total_time*0.75:
            score *= 1.1
        else:
            score *= 1.0
        return score, answered_correctly



