from repositories.quiz_repository import QuizRepository


class QuizService:
    def __init__(self):
        self.quiz_repository = QuizRepository()

    def get_quiz(self, quiz_id):
        return self.quiz_repository.get_quiz(quiz_id)

    def add_quiz(self):
        #TODO implementar el servicio de IA para generar un quiz
        pass

    def update_quiz(self, quiz: dict):
        return self.quiz_repository.update_quiz(quiz)