import random
import traceback
import requests
from telegram.ext import Updater
from telegram.ext import MessageHandler, Filters, CommandHandler
from telegram import ReplyKeyboardMarkup, ParseMode
from collections import deque
from typing import List
import json

TOKEN = '***'
JSON_QUESTIONS_URL = 'https://raw.githubusercontent.com/IrinaShmonina/WhereLogic/master/document.json'

LEVELS_COUNT = 3
ROUNDS_COUNT = 1

HELP_MESSAGE = 'Помоги мне!'
GIVE_UP_MESSAGE = 'Я не знаю('


class Question:
    def __init__(self, question: str, photo: str, answer: str, level: int, accept: str):
        self.question = question
        self.photo = photo
        self.answer = answer
        self.level = level
        self.accept = accept


class QuestionStorage:
    def __init__(self, json_url: str):
        self.url = json_url
        with open('document.json', encoding='utf8') as fp:
            self.json = json.loads(fp.read())  # requests.get(self.url).json()

    def get_questions(self, level: int) -> List[Question]:
        array = self.json['array']
        questions = []
        for q in array:
            if 'level' not in q:
                q['level'] = 1
            if q['level'] == level:
                questions.append(Question(
                    q['question'],
                    q['photo'],
                    q['answer'],
                    q['level'],
                    q['accept'] if 'accept' in q else None
                ))

        return questions


class GameMessage:
    def __init__(self, text=None, photo=None, keyboard=None):
        self.text = text
        self.photo = photo
        self.keyboard = keyboard


class Game:
    def __init__(self, question_storage: QuestionStorage):
        self.question_storage = question_storage
        self._level = 1
        self._round = 1
        self._is_over = False
        self._current_question = None  # type: Question
        self._messages = deque()
        self._used_questions = set()

        self._add_text('Итакс.... Начинаем игру!!')

    def _add_message(self, message: GameMessage):
        self._messages.append(message)

    def _add_text(self, text):
        self._add_message(GameMessage(text=text))

    def next_question(self):
        questions = self.question_storage.get_questions(self._level)
        available_questions = [quest for quest in questions if quest.photo not in self._used_questions]
        if not available_questions:
            self._add_message(GameMessage(
                text='Вопросы закончились =( Ты проиграл!',
                keyboard=[['Начать играть!']]
            ))
            self._is_over = True
            return

        q = random.choice(available_questions)
        self._used_questions.add(q.photo)
        self._add_message(GameMessage(
            text=q.question,
            photo=q.photo,
            keyboard=[[HELP_MESSAGE, GIVE_UP_MESSAGE]]))
        self._current_question = q

    def set_answer(self, answer):
        correct = answer.lower() == self._current_question.answer.lower()

        if correct:
            self._add_message(GameMessage(text='Да, правильно!'))
            self._add_message(GameMessage(photo=self._current_question.accept))
            self._round += 1
            if self._round > ROUNDS_COUNT:
                self._level += 1
                self._round = 1
                if self._level > LEVELS_COUNT:
                    self._add_message(GameMessage(text='Поздравляю! Все уровни пройдены!', keyboard=[['Давай по новой!']]))
                    self._is_over = True
                else:
                    self._add_message(GameMessage(text='Переходим на следующий уровень!'))

        else:
            self._add_message(GameMessage(text='Нет! Попробуй еще раз.'))

        return correct

    def request_help(self):
        self._add_text('Ну даже не знаю, полумай в сторону: ' + self._current_question.answer)

    def give_up(self):
        self._add_text('Ну ладно, ответ: ' + self._current_question.answer)
        self.next_question()

    def has_messages(self):
        return len(self._messages) != 0

    def read_message(self):
        return self._messages.popleft()

    def is_over(self):
        return self._is_over


class BotBase:
    question_storage = QuestionStorage(JSON_QUESTIONS_URL)
    games = {}

    def handle_text(self, chat_id, text, send_output):
        games = self.games
        if chat_id in games:
            game = games[chat_id]
            if text == HELP_MESSAGE:
                game.request_help()
            elif text == GIVE_UP_MESSAGE:
                game.give_up()
            elif game.set_answer(text) and not game.is_over():
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

            if game_message.text:
                bot.send_message(
                    chat_id=chat_id,
                    text=game_message.text,
                    reply_markup=ReplyKeyboardMarkup(game_message.keyboard, resize_keyboard=True) if game_message.keyboard else None,
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
