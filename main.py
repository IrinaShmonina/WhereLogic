import requests
cur_id = 0
while True:
    r = requests.post('https://api.telegram.org/bot706745232:AAFALlvYfsHPd51a2WpXAt--arGb5m_q3mk/getupdates',data={'offset':cur_id+1})
    if r.json()['result']:
        cur_id = r.json()['result'][-1]['update_id']
        chat_id = r.json()['result'][-1]['message']['chat']['id']
        text = r.json()['result'][-1]['message']['text']
        r = requests.post('https://api.telegram.org/bot706745232:AAFALlvYfsHPd51a2WpXAt--arGb5m_q3mk/sendMessage',
                          data = {'chat_id':chat_id,'text':text})
        r = requests.post('https://api.telegram.org/bot706745232:AAFALlvYfsHPd51a2WpXAt--arGb5m_q3mk/sendphoto',
                          data={'chat_id': chat_id, 'photo': 'https://i.ytimg.com/vi/-qj4O2aHQqc/maxresdefault.jpg'})

    print(r.json())
