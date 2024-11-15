from fastapi import HTTPException
from repositories.quiz_repository import QuizRepository
import requests
from core.app_settings import get_settings
from services.resource_service import ResourceService



settings = get_settings()


def process_quiz_data(quiz: dict):
    # Procesar preguntas y opciones
    questions = []
    all_answers = []
    correct_answers = []

    # Iterar sobre las preguntas
    for question_text in quiz["questions"]:
        # Extraer solo el texto de la pregunta, eliminando el número y el punto
        question_text_only = question_text.split(" ", 1)[1].strip()

        # Añadir la pregunta formateada a la lista
        questions.append({"question": question_text_only})

    # Iterar sobre las opciones
    for option_set in quiz["options"]:
        # Inicializar las opciones en vacío
        option_a, option_b, option_c, option_d = "", "", "", ""

        # Dividir las opciones usando los prefijos si están presentes
        options_text = option_set["options"]

        if "A-" in options_text:
            option_a = "A-" + options_text.split("A-")[1].split("B-")[0].strip()
        if "B-" in options_text:
            option_b = "B-" + options_text.split("B-")[1].split("C-")[0].strip()
        if "C-" in options_text:
            option_c = "C-" + options_text.split("C-")[1].split("D-")[0].strip()
        if "D-" in options_text:
            option_d = "D-" + options_text.split("D-")[1].strip()

        # Añadir las opciones de respuesta a la lista
        all_answers.append([option_a, option_b, option_c, option_d])

    # Iterar sobre las respuestas correctas
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
            data = self.quiz_repository.get_quiz_founder(resource_id)
            print(data)
            return data
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

            # Verifica que la estructura del JSON sea la esperada
            if "questions" not in data_quiz or "answers" not in data_quiz:
                raise HTTPException(status_code=500, detail="IA_API response is not valid")
            data_quiz = process_quiz_data(data_quiz)  # Procesa el JSON obtenido
            self.quiz_repository.save_quiz(resource_id, data_quiz)  # Guarda el quiz en la base de datos
            return data_quiz  # Retorna el JSON con la estructura obtenida

        except Exception as e:
            raise HTTPException(status_code=500, detail="Error while getting quiz from AI_API: " + str(e))

    def get_quiz_member(self, resource_id: int):
        return self.quiz_repository.get_quiz_founder(resource_id)
    def quiz_exists(self, resource_id: int):
        return self.quiz_repository.quiz_exists(resource_id)
    def update_quiz(self, resource_id: int,quiz: dict):
        return self.quiz_repository.update_quiz(resource_id, quiz)



