import unittest
from main import QuestionStorage, GameMessage, Game, Question


class QuestionStorageTests(unittest.TestCase):
    def setUp(self):
        self.storage = QuestionStorage('')

    def test_storage_is_not_empty(self):
        self.storage = QuestionStorage('')
        questions = self.storage.get_questions(self.storage.min_level)  # получаем вопросы первого уровня
        self.assertGreater(len(questions), 0) 

    def test_get_questions_more_than_max_level(self):
        max_level = self.storage.max_level  

        questions = self.storage.get_questions(max_level + 1)

        self.assertLessEqual(len(questions), 0)

    def test_get_questions_less_than_min_level(self):
        min_level = self.storage.min_level

        questions = self.storage.get_questions(min_level - 1)

        self.assertLessEqual(len(questions), 0)


class GameMessageTests(unittest.TestCase):
    def test_message_created(self):
        message = GameMessage()
        self.assertIsNotNone(message)


class QuestionTests(unittest.TestCase):
    def test_question_created(self):
        question = Question('Вопрос?', 'photo', 'answer', level=1, accept='')
        self.assertIsNotNone(question)
        self.assertEqual(question.question, 'Вопрос?')


class GameTests(unittest.TestCase):
    def setUp(self):
        self.questions_storage = QuestionStorage('')
        self.game = Game(self.questions_storage)

    def test_game_created(self):
        self.assertIsNotNone(self.game)
        self.assertFalse(self.game.is_over())
        self.assertTrue(self.game.has_messages())

    def test_game_has_end(self):
        while not self.game.is_over():
            self.game.next_question()
        self.assertTrue(self.game.is_over())

    def test_request_help_adds_messages(self):
        self.game = Game(self.questions_storage)
        self.game.next_question()
        start_messages_count = self.game.get_messages_count()

        self.game.request_help()

        self.assertGreater(self.game.get_messages_count(), start_messages_count)

    def test_read_message_decreases_messages_count(self):
        self.game = Game(self.questions_storage)
        self.game.next_question()
        start_messages_count = self.game.get_messages_count()

        self.game.read_message()

        self.assertLess(self.game.get_messages_count(), start_messages_count)


if __name__ == '__main__':
    unittest.main()
