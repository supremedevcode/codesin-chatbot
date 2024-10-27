import json
import logging
from flask import Flask, jsonify, render_template, request
from flask_sqlalchemy import SQLAlchemy
from datetime import timezone, datetime as dt

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
  return jsonify({'message': 'EVENT_RECEIVED'})

if __name__=='__main__':
  app.run(host='0.0.0.0', port=80, debug=True)
