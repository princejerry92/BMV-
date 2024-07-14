import requests

API_KEY = '7066419692:AAH8T0_7ZUZ9b6_JJXZpjRYgdtkVfzLQ3hc'
CHAT_ID = '-1002202263732'

def send_message(text):
    url = f'https://api.telegram.org/bot{API_KEY}/sendMessage'
    data = {
        'chat_id': CHAT_ID,
        'text': text
    }
    response = requests.post(url, data=data)
    if response.status_code == 200:
        print('Message sent successfully!')
    else:
        print(f'Failed to send message. Error code: {response.status_code}')
