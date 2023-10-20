import os
from cs50 import SQL
from flask import Flask, flash, url_for, redirect, render_template, request, session, Response
from datetime import datetime
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
from flask_socketio import SocketIO, emit
# Configure application
app = Flask(__name__)
app.config["SECRET_KEY"] = "your-secret-key"  # Add a secret key for security
app.debug = True
socketio = SocketIO(app)
# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)
# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///Quack.db")

@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html", massege="")
    elif request.method == "POST":
        country = request.form.get("country")
        if country not in ["eg", "us"]:
            return render_template("login.html", massege="INVALID COUNTRY")
        if not request.form.get("phone"):
            return render_template("login.html", massege="EMPTY USERNAME")
        # Ensure password was submitted
        elif not request.form.get("password"):
            return render_template("login.html", massege="EMPTY PASSWORD")

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE number = ? AND country = ?", request.form.get("phone"), country
        )

        # Ensure username exists and password is correct
        if len(rows) != 1:
            return render_template("login.html", massege="INVALID USERNAME AND/OR PASSWORD AND/OR COUNTRY")

        # Remember which user has logged in
        session["user_id"] = rows[0]["user_id"]
        session["name"] = rows[0]["name"]

        # Redirect user to home page
        return redirect("/")

@app.route('/logout')
def logout():
    session.clear()
    return redirect("/login")


@app.route('/signup', methods=["POST", "GET"])
def signup():
    if request.method == "GET":
        return render_template("signup.html", massege="")
    elif request.method == "POST":
        country = request.form.get("country")
        if request.form.get("country") not in ["eg", "us"]:
            return render_template("signup.html", massege="INVALID COUNTRY")
        password = request.form.get("password")
        phone = request.form.get("phone")
        name = request.form.get("name")
        rows = db.execute("SELECT number, name FROM users")
        for row in rows:
            if phone == row["number"]:
                return render_template("signup.html", massege="PHONE NUMBER ALREADY LINKED")
        for row in rows:
            if name == row["name"]:
                return render_template("signup.html", massege="USER NAME USED")

        if password == "" or phone == "" or name == "":
            return render_template("signup.html", massege="EMPTY PHONE NUMBER, NAME AND/OR PASSWORD")
        if len(phone) != 11:
            return render_template("signup.html", massege="invalid number")

    db.execute("INSERT INTO users (number, password, country, name) VALUES (?, ?, ?, ?)", phone, password, country, request.form.get("name"))
    return render_template("login.html", massege="")
@app.route('/search', methods=['GET', 'POST'])
def search():
    name = request.form.get("name")
    if name == "":
        return Response(status=204)
    names = db.execute("SELECT * FROM users WHERE name LIKE '%' || ? || '%' AND user_id != ?", name, session["user_id"])
    if len(names) == 0:
        msg = "no names found"
        code = 0
        return render_template("index.html", msg=msg, code=code, names=names)
    else:
        code = 1
        return render_template("index.html", msg="", code=code, names=names, user=session["name"])


@app.route('/chat/<username>')
def chat(username):
    user = db.execute("SELECT name FROM users WHERE name = ?", username)
    if len(user) == 0:
        return redirect("/") 
    session["reciever"] = username
    return render_template("chat.html", name=username)


@app.route('/')
def home():
    if session.get("user_id") is not None:
        return render_template("index.html")
    else:
        return redirect("/login")
    

users = {}  # Global dictionary

@socketio.on('connect')
def handle_connect():
    username = db.execute("SELECT name FROM users WHERE user_id = ?", session["user_id"])[0]["name"]
    users[username] = request.sid
    msgs = db.execute("SELECT msg, sender, timestamp FROM msgs WHERE (reciever = ? AND sender = ?) OR (reciever = ? AND sender = ?) ORDER BY timestamp", session["reciever"], username, username, session["reciever"])
    print(msgs)
    for msg in msgs:
        if msg['sender'] == username:
           emit('message', {'msg': msg['msg'], 'timestamp': msg["timestamp"]}, room=users[username])
        else:
            emit('message1', {'msg': msg['msg'], 'timestamp': msg["timestamp"]}, room=users[username])

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

@socketio.on('message')
def handle_message(data):
    reciever_id = db.execute("SELECT user_id FROM users WHERE name = ?", data['recipient'])[0]["user_id"]
    name = db.execute("SELECT name FROM users WHERE user_id = ?", session["user_id"])[0]["name"]
    now = datetime.now()
    now_str = now.strftime('%Y-%m-%d %H:%M:%S')
    db.execute("INSERT INTO msgs (msg, reciever, reciever_id, sender, sender_id, timestamp) VALUES(?, ?, ?, ?, ?, ?)", data["msg"], data['recipient'], reciever_id, name, session["user_id"], now_str)
    if data["recipient"] in users:
        recipient_session_id = users[data['recipient']]
        emit('message', data['msg'], room=recipient_session_id)


if __name__ == '__main__':
    socketio.run(app)