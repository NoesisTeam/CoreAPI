from fastapi import HTTPException
from repositories.quiz_repository import QuizRepository
import requests
from core.app_settings import get_settings
from services.resource_service import ResourceService



settings = get_settings()
def process_quiz_data(quiz: dict):
    # Procesar preguntas y opciones
    questions = []
    correct_answers = []
    all_answers = []

    for i, question_text in enumerate(quiz["questions"], start=1):
        # Dividir en pregunta y opciones
        question_split = question_text.split(" ")
        question_text_only = " ".join(question_split[1:]).split(" A-")[0].strip()

        # Separar opciones y almacenar en un arreglo
        options = question_text.split(" A-")[1].split(" B-")
        option_a = "A-" + options[0].strip()
        options_rest = options[1].split(" C-")
        option_b = "B-" + options_rest[0].strip()
        options_rest = options_rest[1].split(" D-")
        option_c = "C-" + options_rest[0].strip()
        option_d = "D-" + options_rest[1].strip()

        # Añadir pregunta formateada y opciones a las listas
        questions.append({
            "question": question_text_only
        })
        all_answers.append([option_a, option_b, option_c, option_d])

    # Procesar respuestas correctas
    for answer in quiz["answers"]:
        correct_answers.append(answer["answer"])

    # Estructurar el diccionario final
    processed_quiz = {
        "questions": questions,
        "answers": all_answers,
        "correct_answers": correct_answers,
        "quantity_questions": len(questions)
    }

    return processed_quiz

class QuizService:
    def __init__(self):
        self.quiz_repository = QuizRepository()
        self.resource_service = ResourceService()

    def get_quiz(self, resource_id: int):
        if self.quiz_repository.quiz_exists(resource_id):
            return self.quiz_repository.get_quiz_founder(resource_id)
        # Si no existe el quiz en la base de datos, se obtiene de la IA_API
        else:
            return self.add_quiz(resource_id)

    def add_quiz(self, resource_id: int):
        try:

            url = settings.AI_API_URL # URL de la API externa
            headers = {
                "Content-Type": "application/json"  # Establece el tipo de contenido a JSON
            }
            data_sent = {
                "resource_url": self.resource_service.get_resource_url(resource_id) # URL del recurso
            }
            response = requests.post(url, headers=headers, json=data_sent)  # Envía el 'data' en formato JSON
            data_quiz = response.json()
            # Verifica la respuesta
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code,
                                    detail="Error while getting quiz from AI_API")
            else:
                print("Error:", response.status_code, response.text)

            # Verifica que la estructura del JSON sea la esperada
            if "questions" not in data_quiz or "answers" not in data_quiz:
                raise HTTPException(status_code=500, detail="IA_API response is not valid")

            data_quiz = process_quiz_data(data_quiz)  # Procesa el JSON obtenido
            self.quiz_repository.save_quiz(resource_id, data_quiz)  # Guarda el quiz en la base de datos
            return data_quiz  # Retorna el JSON con la estructura obtenida

        except Exception as e:
            raise HTTPException(status_code=500, detail="Error while getting quiz from AI_API" + str(e))

    def get_quiz_member(self, resource_id: int):
        return self.quiz_repository.get_quiz_founder(resource_id)
    def quiz_exists(self, resource_id: int):
        return self.quiz_repository.quiz_exists(resource_id)
    def update_quiz(self, resource_id: int,quiz: dict):
        return self.quiz_repository.update_quiz(resource_id, quiz)



