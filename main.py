import json
import logging

from flask import Flask, jsonify, render_template, request
from flask_sqlalchemy import SQLAlchemy
from datetime import timezone, datetime as dt
import http.client as http_client

logger = logging.getLogger(__name__)

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///codesin.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# model of the table log
class Log(db.Model):
  id=db.Column(db.Integer, primary_key=True)
  date_time=db.Column(db.DateTime, default=dt.now(timezone.utc))
  text=db.Column(db.TEXT)
  
# Create table if not exists
with app.app_context():
  db.create_all()
  
# Function to order rows by datetime
def sort_by_datetime(rows):
  return sorted(rows, key=lambda x: x.date_time, reverse=True)

@app.route("/")
def index():
  # get all rows of the data bases
  rows = Log.query.all()
  sorted_rows = sort_by_datetime(rows)
  return render_template('index.html', rows=sorted_rows)

log_messages = []

# Function to add messages and save in the data bases
def add_messages_log(text):
  log_messages.append(text)
  
  # Save message in the data bases
  new_row = Log(text=text)
  db.session.add(new_row)
  db.session.commit()

TOKEN_SUPREMEDEVCODE = "SUPREMEDEVCODE"

@app.route("/webhook", methods=["GET","POST"])
def webhook():
  logger.info("incoming request from customer.")
  if request.method == 'GET':
    challenge = token_verification(request)
    return challenge
  elif request.method == 'POST':
    response = receive_messages(request)
    return response
  
def token_verification(req):
  logger.info("verifying the token.")
  token = req.args.get('hub.verify_token')
  challenge = req.args.get('hub.challenge')
  if challenge and token == TOKEN_SUPREMEDEVCODE:
    return challenge
  else:
    return jsonify({'error':'Invalid token'}), 401

def receive_messages(req):
  logger.info("receiving the messages.")
  req_data = req.get_json()
  req_json = json.dumps(req_data)
  add_messages_log(req_json)
  try:
    req_data = req.get_json()
    entry = req_data["entry"][0]
    changes = entry["changes"][0]
    value = changes["value"]
    if "messages" in value:
      object_message = value["messages"]
      if object_message:
        message = object_message[0]
        if "type" in message:
          type_ = message["type"]
          if type_ == "interactive":
            return 0
          if "text" in message:
            text = message["text"]["body"]
            number = message["from"]
            send_messages_whatsapp(text_msg=text, phone_number=number)
            add_messages_log(json.dumps(text))
            add_messages_log(json.dumps(number))
            
    return jsonify({'message': 'EVENT_RECEIVED'})
  except Exception as e:
    logger.exception("Error receiving messages: ", e)
    return jsonify({'message': 'EVENT_RECEIVED'})

def send_messages_whatsapp(text_msg, phone_number):
  text = text_msg.lower()
  if "hola" in text:
    data = {
      "messaging_product": "whatsapp",
      "recipient_type": "individual",
      "to": phone_number,
      "type": "text",
      "text": {
        "preview_url": False,
        "body": "\uD83D Hola, ¿Cómo estás? Bienvenido."
      }
    }
  else:
    data = {
      "messaging_product": "whatsapp",
      "recipient_type": "individual",
      "to": phone_number,
      "type": "text",
      "text": {
        "preview_url": False,
        "body": "\uD83D Hola, visita mi web codesinconsultoria.com para más información."
      }
    }

  data = json.dumps(data)
  
  headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer EAAGXou2wA7YBO4zB7fKouVvuaG2030L6tl5b24ZBdOZAhQnHB4X7PO2b5KLokfRo4zgbpYdkGTya69SHjKSsmRoJLorSogoy8rcF7YBSBKSNJSZBZCKbrhhaBIV9TAz5NqZB1mNJyM228awbY2ostxs8sqGR5rPUPfSG8ST10UMVjOIyLRR7CikBegKODsktx0ZBuqdztBc9689EX7k6Vx2NHGPZAtn2liLNb8ZD"
  }
  
  connection = http_client.HTTPSConnection("graph.facebook.com")
  
  try:
    connection.request("POST", "/v21.0/388973824307193/messages", data, headers)
    response = connection.getresponse()
    logger.info(response.status, response.reason)
  except Exception as e:
    add_messages_log(json.dumps(e))
  finally:
    connection.close()

if __name__=='__main__':
  app.run(host='0.0.0.0', port=80, debug=True)
