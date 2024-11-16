import json
from fastapi import HTTPException
from repositories.quiz_repository import QuizRepository
import requests
from core.app_settings import get_settings
from services.resource_service import ResourceService



settings = get_settings()


import json

def process_quiz_data(quiz_json):
    try:
        if isinstance(quiz_json, str):
            quiz = json.loads(quiz_json)
        else:
            quiz = quiz_json

        # Verificar que el formato de quiz es correcto
        if not all(key in quiz for key in ["questions", "options", "answers"]):
            raise ValueError("El JSON debe contener las claves 'questions', 'options' y 'answers'.")

        # Inicializar estructuras de datos
        questions = []
        all_answers = []
        correct_answers = []

        # Procesar preguntas
        for question_text in quiz["questions"]:
            if not isinstance(question_text, str):
                raise ValueError(f"Las preguntas deben ser cadenas. Encontrado: {type(question_text)}")
            # Extraer el texto de la pregunta eliminando el número y el punto
            question_text_only = question_text.split(" ", 1)[1].strip()
            questions.append({"question": question_text_only})

        # Procesar opciones
        for option_set in quiz["options"]:
            if "options" not in option_set:
                raise ValueError("Cada conjunto de opciones debe tener una clave 'options'.")
            options_text = option_set["options"]
            if not isinstance(options_text, str):
                raise ValueError(f"Las opciones deben ser cadenas. Encontrado: {type(options_text)}")

            options = {
                "A": None,
                "B": None,
                "C": None,
                "D": None
            }
            # Extraer cada opción
            if "A-" in options_text:
                options["A"] = "A-" + options_text.split("A-")[1].split("B-")[0].strip()
            if "B-" in options_text:
                options["B"] = "B-" + options_text.split("B-")[1].split("C-")[0].strip()
            if "C-" in options_text:
                options["C"] = "C-" + options_text.split("C-")[1].split("D-")[0].strip()
            if "D-" in options_text:
                options["D"] = "D-" + options_text.split("D-")[1].strip()
            all_answers.append([options["A"], options["B"], options["C"], options["D"]])

        # Procesar respuestas correctas
        for answer in quiz["answers"]:
            if "answer" not in answer:
                raise ValueError("Cada respuesta debe tener una clave 'answer'.")
            correct_answers.append(answer["answer"])

        # Estructurar el diccionario final
        processed_quiz = {
            "questions": questions,
            "answers": all_answers,
            "correct_answers": correct_answers,
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

    def get_quiz(self, resource_id: int):
        if self.quiz_repository.quiz_exists(resource_id):
            data = self.quiz_repository.get_quiz(resource_id)
            return data
        # Si no existe el quiz en la base de datos, se obtiene de la IA_API
        else:
            quiz = self.get_data(resource_id)
            self.quiz_repository.save_quiz(resource_id, quiz)
            return quiz

    def get_data(self, resource_id: int):

        try:

            url = settings.AI_API_URL # URL de la API externa
            headers = {
                "Content-Type": "application/json"  # Establece el tipo de contenido a JSON

            }
            data_sent = {
                "resource_url": self.resource_service.get_resource_url(resource_id) # URL del recurso
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

    def get_quiz_member(self, resource_id: int):
        if not self.quiz_repository.quiz_exists(resource_id):
            raise HTTPException(status_code=404, detail="Quiz not found")
        return self.quiz_repository.get_quiz(resource_id)
    def regen_quiz(self, resource_id: int):
        quiz = self.get_data(resource_id)
        self.quiz_repository.regen_quiz(resource_id, quiz)
        return quiz



