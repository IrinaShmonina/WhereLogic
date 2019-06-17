import traceback
from telegram.ext import Updater
from telegram.ext import MessageHandler, Filters, CommandHandler
from telegram import ReplyKeyboardMarkup, ParseMode
from collections import deque
from typing import List
import json
import psycopg2
import requests
import random
import io
import sys

TG_TOKEN = '706745232:AAFALlvYfsHPd51a2WpXAt--arGb5m_q3mk'
VK_TOKEN = 'c7b5a6a37b707e62b9f78d81c1b53076e2907621fde92ec8ef75c75e0584e1c4f9c0c4afc2d5bde0ea16c'
VK_GROUP_ID = '183568730'
PSQL_CONNECTION_STRING = 'postgres://sduggktd:xMXjBx0bvCZ-dAwsdiE5bJH-v3idWARj@raja.db.elephantsql.com:5432/sduggktd'
GAME_DATABASE_NAME = 'game'

LEVELS_COUNT = 2
ROUNDS_COUNT = 2

HELP_MESSAGE = 'Помоги мне!'
GIVE_UP_MESSAGE = 'Я не знаю('


class Question:
    def __init__(self, question: str, photo: str, answer: str, level: int, accept: str, hint: str):
        self.question = question
        self.photo = photo
        self.answer = answer
        self.level = level
        self.accept = accept
        self.hint = hint


class QuestionStorage:
    def __init__(self, db):
        self.db = db

    def get_questions(self, level: int) -> List[Question]:
        curr = self.db.cursor()
        sql_request = "SELECT question, photo, answer, level, accept, hint FROM game WHERE level={}".format(level)
        curr.execute(sql_request)
        questions = list(map(lambda x: Question(*x), curr.fetchall()))
        return questions

    def store_question(self, q: Question):
        curr = self.db.cursor()
        sql_request = "INSERT INTO {} (question, photo, hint, answer, accept, level) VALUES ('{}', '{}', '{}', '{}', {}, {})".format(GAME_DATABASE_NAME, q.question, q.photo,
                                                                          q.hint, q.answer,
                                                                          "'" + q.accept + "'" if q.accept else "NULL",
                                                                          q.level)
        curr.execute(sql_request)
        self.db.commit()
        curr.close()


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
        self._add_text(self._current_question.hint)

    def give_up(self):
        self._add_text('Ну ладно, ответ: ' + self._current_question.answer)
        self.next_question()

    def has_messages(self):
        return len(self._messages) != 0

    def read_message(self):
        return self._messages.popleft()

    def is_over(self):
        return self._is_over

    def get_messages_count(self):
        return len(self._messages)


class BotBase:
    games = {}

    def __init__(self, storage: QuestionStorage):
        self.question_storage = storage

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

        updater = Updater(token=TG_TOKEN)
        dispatcher = updater.dispatcher
        dispatcher.add_handler(MessageHandler([Filters.text], handle_message))

        updater.start_polling()

class VkBot(BotBase):
    def _authorize(self):
        params = self._call_vk_method('groups.getLongPollServer', params={'group_id': VK_GROUP_ID})

        self.key = params['key']
        self.server = params['server']
        self.ts = params['ts']

    def _poll(self):
        resp = requests.get('{}?act=a_check&key={}&ts={}&wait=25)'.format(self.server, self.key, self.ts))
        if resp.ok:
            json_resp = resp.json()
            print('POLL: ', json_resp)
            self.ts = json_resp['ts']
            updates = json_resp['updates']
            return [update['object'] for update in updates if update['type'] == 'message_new']
        return []

    def _send_message(self, chat_id, game_message: GameMessage):
        if game_message.photo:
            upload_response = self._call_vk_method('photos.getMessagesUploadServer', params={'peer_id': chat_id})
            upload_url = upload_response['upload_url']
            image_bytes = requests.get(game_message.photo).content
            upload_result = requests.post(upload_url, files={'photo': ('photo.jpg', io.BytesIO(image_bytes))}).json()
            photo_meta = self._call_vk_method('photos.saveMessagesPhoto', params=upload_result)[0]

            self._call_vk_method('messages.send', params={
                'user_id': chat_id,
                'random_id': random.randint(0, 2 ** 32),
                'attachment': 'photo{}_{}'.format(photo_meta['owner_id'], photo_meta['id']),
            })

        if game_message.text:
            keyboard = self._make_vk_keyboard(game_message.keyboard)
            print(keyboard)
            self._call_vk_method('messages.send', params={
                'user_id': chat_id,
                'random_id': random.randint(0, 2**32),
                'message': game_message.text,
                'keyboard': keyboard
            })

    def _make_vk_keyboard(self, msg_keyboard):
        if not msg_keyboard:
            return None
        vk_keyboard = []
        for line in msg_keyboard:
            vk_keyboard.append([{'action': {'type': 'text', 'label': value}} for value in line])
        return json.dumps({
            'one_time': False,
            'buttons': vk_keyboard
        }, separators=(',', ':'), ensure_ascii=False)

    def _start_polling(self):
        while True:
            for new_message in self._poll():
                chat_id = new_message['from_id']
                text = new_message['text']
                self.handle_text(chat_id, text, self._send_message)

    def _call_vk_method(self, method: str, params):
        params['access_token'] = VK_TOKEN
        params['v'] = '5.95'
        resp = requests.get(
            'https://api.vk.com/method/{}'.format(method),
            params=params).json()
        print('CALL: ', resp)

        return resp['response']

    def run(self):
        self._authorize()
        self._start_polling()



def initialize_database(storage: QuestionStorage):
    with open('document.json', encoding='utf8') as fp:
        questions_json = json.loads(fp.read())
        array = questions_json['array']
        for q in array:
            if 'level' not in q:
                q['level'] = 1
            question = Question(
                q['question'],
                q['photo'],
                q['answer'],
                q['level'] if 'level' in q else 1,
                q['accept'] if 'accept' in q else None,
                q['hint']
            )
            storage.store_question(question)


if __name__ == '__main__':
    db = psycopg2.connect(PSQL_CONNECTION_STRING)
    question_storage = QuestionStorage(db)

    if sys.argv[1] == 'tg':
        print('start Telegram bot')
        bot = TelegramBot(question_storage)
    elif sys.argv[1] == 'vk':
        print('start VK bot')
        bot = VkBot(question_storage)
    else:
        print('Please provide bot system as first argument: "vk" or "tg"')
        exit(1)
    bot.run()
