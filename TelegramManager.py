import requests
from Configuration import Configuration

config = Configuration()

BOT_TOKEN = config.email
CHAT_ID = config.recipientEmail
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/"

def send_message(text: str):
    try:
        url = BASE_URL + "sendMessage"
        data = {
            "chat_id": CHAT_ID,
            "text": text
        }
        response = requests.post(url, data=data)
        if config.debug:
            print("Messaggio Telegram inviato:", response.status_code)
    except Exception as e:
        if config.debug:
            print("Errore invio messaggio:", e)


def send_file(filepath: str, caption=""):
    try:
        url = BASE_URL + "sendDocument"
        with open(filepath, "rb") as f:
            files = {'document': f}
            data = {"chat_id": CHAT_ID, "caption": caption}
            response = requests.post(url, files=files, data=data)
        if config.debug:
            print("File inviato:", response.status_code)
    except Exception as e:
        if config.debug:
            print("Errore invio file:", e)
