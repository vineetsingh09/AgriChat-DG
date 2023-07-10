import json
import tornado.ioloop
import tornado.web
import requests
# from utils.utils import get_user
# from whatsapp_utils import get_user
# import whatsapp_utils
# import utils
import os

VERIFY_TOKEN= os.environ["VERIFY_TOKEN"]
WHATSAPP_TOKEN = os.environ["WHATSAPP_TOKEN"]
WHATSAPP_URL = os.environ["WHATSAPP_URL"]

class MyApplication(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/webhook/cb6a9b81-e30e-46e3-893d-cc28e2d16672", MainHandler),
            # Add more request handlers as needed
        ]
        settings = {
            # Configure Tornado settings (if any)
        }
        super().__init__(handlers, **settings)

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        mode = self.get_query_argument('hub.mode')
        token = self.get_query_argument('hub.verify_token')
        challenge = self.get_query_argument('hub.challenge')

        # print(mode, token, challenge)
        try:
            if mode == 'subscribe' and token == VERIFY_TOKEN:
                self.set_status(200)
                self.write(challenge)
            else:
                self.set_status(403)
                self.write("Not from Facebook API")
        except Exception as err:
            self.set_status(400)
            self.write("Something went wrong")

    @classmethod
    def send_whatsapp_message(self, phone_number, message_to_send):
        headers = {"Authorization": WHATSAPP_TOKEN}
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": phone_number,
            "type": "text",
            "text": {"body":  message_to_send
            }
        }
        res = requests.post(WHATSAPP_URL, headers=headers, json=payload)
        print(res)
        return res.json()

    def post(self):
        text = None
        from_id = None
        phone_number= None
        phone_id = None
        profile_name=  None
        whatsapp_id = None
        message_id= None
        timestamp = None
        
        data = json.loads(self.request.body)
        # print(data)
        if 'object' in data and 'entry' in data:
            if data['object'] == 'whatsapp_business_account':
                try:
                    for entry in data['entry']:
                        print("data received")
                        phone_number = entry['changes'][0]['value']['metadata']['display_phone_number']
                        phone_id = phone_number = entry['changes'][0]['value']['metadata']['phone_number_id']
                        profile_name = entry['changes'][0]['value']['contacts'][0]['profile']['name']
                        whatsapp_id = entry['changes'][0]['value']['contacts'][0]['wa_id']
                        from_id = entry['changes'][0]['value']['messages'][0]['from']
                        message_id = entry['changes'][0]['value']['messages'][0]['id']
                        timestamp = entry['changes'][0]['value']['messages'][0]['timestamp']
                        text = entry['changes'][0]['value']['messages'][0]['text']['body']
                except Exception as err:
                    print("Error Received", err)
        # print(phone_number, phone_id, profile_name, whatsapp_id, message_id, timestamp, from_id, text)
        phone_number = from_id
        if text and phone_number:
            self.send_whatsapp_message(phone_number, text)
            self.set_status(200)

if __name__ == "__main__":
    app = MyApplication()
    app.listen(8000)  # Set the desired port number
    tornado.ioloop.IOLoop.current().start()
