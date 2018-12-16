import random
import traceback
import requests
from telegram.ext import Updater
from telegram.ext import MessageHandler, Filters, CommandHandler
from telegram import ReplyKeyboardMarkup, ParseMode
from collections import deque

TOKEN = '706745232:AAFALlvYfsHPd51a2WpXAt--arGb5m_q3mk'
JSON_QUESTIONS_URL = 'https://raw.githubusercontent.com/IrinaShmonina/WhereLogic/master/document.json'


class Question:
    def __init__(self, question, photo, answer, level):
        self.question = question
        self.photo = photo
        self.answer = answer
        self.level = level


class QuestionStorage:
    def __init__(self, json_url):
        self.url = json_url
        self.json = requests.get(self.url).json()

    def get_questions(self, level) -> [Question]:
        array = self.json['array']
        questions = [Question(q['question'], q['photo'], q['answer'], 1) for q in array] #todo filter by level

        return questions


class GameMessage:
    def __init__(self, text=None, photo=None, keyboard=None):
        self.text = text
        self.photo = photo
        self.keyboard = keyboard


class Game:
    _level = 1
    _turn = 1
    _is_over = False
    _current_question = None  # type: Question
    _messages = deque()
    _i = -1

    def __init__(self, question_storage: QuestionStorage):
        self.question_storage = question_storage

    def _add_message(self, message: GameMessage):
        self._messages.append(message)

    def next_question(self):
        self._i += 1
        self._i %= 10

        q = self.question_storage.get_questions(self._level)[self._i]
        self._add_message(GameMessage(text=q.question, photo=q.photo))
        self._current_question = q

    def set_answer(self, answer):
        correct = answer.lower() == self._current_question.answer.lower()

        if not correct:
            self._add_message(GameMessage(text='Нет! Попробуй еще раз.'))
        else:
            self._add_message(GameMessage(text='Да, правильно!'))

        return correct

    def has_messages(self):
        return len(self._messages) != 0

    def read_message(self):
        return self._messages.popleft()

    def is_over(self):
        return False


class BotBase:
    question_storage = QuestionStorage(JSON_QUESTIONS_URL)
    games = {}

    def handle_text(self, chat_id, text, send_output):
        games = self.games
        if chat_id in games:
            game = games[chat_id]
            if text == 'Помоги мне!':
                game.request_help()
            elif game.set_answer(text):
                game.next_question()
            if game.is_over():
                del games[chat_id]
        else:
            game = Game(self.question_storage)
            games[chat_id] = game
            game.next_question()
        while game.has_messages():
            message = game.read_message()
            send_output(chat_id, message)

    def run(self):
        raise NotImplementedError


class TelegramBot(BotBase):
    def run(self):
        def send_message(bot, chat_id, game_message: GameMessage):
            if game_message.photo:
                bot.send_photo(
                    chat_id=chat_id,
                    photo=game_message.photo
                )
            if game_message.text:  # todo keyboard
                bot.send_message(
                    chat_id=chat_id,
                    text=game_message.text,
                    parse_mode=ParseMode.MARKDOWN
                )

        def handle_message(bot, update):
            try:
                print('FROM: {}, TEXT: {}'.format(update.message.chat_id, update.message.text))
                chat_id = update.message.chat_id
                text = update.message.text
                self.handle_text(chat_id, text, lambda cid, msg: send_message(bot, cid, msg))
            except Exception:
                traceback.print_exc()

        updater = Updater(token=TOKEN)
        dispatcher = updater.dispatcher
        dispatcher.add_handler(MessageHandler([Filters.text], handle_message))

        updater.start_polling()


if __name__ == '__main__':
    bot = TelegramBot()

    bot.run()
