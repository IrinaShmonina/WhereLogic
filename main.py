import requests

cur_id = 0
status = {}
st_question = 'question'
st_answer = 'answer'
st_done = 'done'
question = ''
photo = ''
answer = ''

q = requests.get('https://raw.githubusercontent.com/IrinaShmonina/WhereLogic/master/document.json').json()

def send_question(chat_id, question, photo):
    r = requests.post('https://api.telegram.org/***/sendMessage',
                      data={'chat_id': chat_id, 'text': question})

    r = requests.post('https://api.telegram.org/***/sendphoto',
                      data={'chat_id': chat_id, 'photo': photo})
    pass


def chice(q):
    section = random.choice(q['array'])
    question = section['question']
    photo = section['photo']
    answer = section['answer']
    return question, photo, answer


while True:
    r = requests.post('https://api.telegram.org/bot706745232:AAFALlvYfsHPd51a2WpXAt--arGb5m_q3mk/getupdates',
                      data={'offset': cur_id + 1})


    for i in r.json()['result']:
        cur_id = i['update_id']
        chat_id = i['message']['chat']['id']
        text = i['message']['text']

        if chat_id not in status:
            r = requests.post('https://api.telegram.org/bot706745232:AAFALlvYfsHPd51a2WpXAt--arGb5m_q3mk/sendMessage',
                              data={'chat_id': chat_id, 'text': 'Привет, друг! '
                                                                'Давай сыграем в игру. В этом раунде тебе необходимо '
                                                                'понять, что между картинками общего или что будет, '
                                                                'если их объединить.'})
            question, photo, answer = chice(q)
            status[chat_id]=Player(st_question,'')
            send_question(chat_id, question, photo)
            status[chat_id] = Player(st_answer,answer)
        elif status[chat_id].status == st_answer:
            if text == status[chat_id].answer:
                r = requests.post(
                    'https://api.telegram.org/bot706745232:AAFALlvYfsHPd51a2WpXAt--arGb5m_q3mk/sendMessage',
                    data={'chat_id': chat_id, 'text': 'Верно!'})
                status[chat_id] = Player(st_done,'')
                question, photo, answer = chice(q)
                send_question(chat_id, question, photo)
                status[chat_id] = Player(st_answer, answer)
            else:
                r = requests.post(
                    'https://api.telegram.org/bot706745232:AAFALlvYfsHPd51a2WpXAt--arGb5m_q3mk/sendMessage',
                    data={'chat_id': chat_id, 'text': 'Нет! Попробуй еще раз.'})
                print(answer)

    print(r.json())
