from flask import Flask, render_template, session, redirect, request
from flask_socketio import SocketIO, emit, join_room, leave_room
from collections import deque

app = Flask(__name__)
app.config["SECRET_KEY"] = "secret"
socketio = SocketIO(app)

app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0 # disable caching

# array storing the list of Chat Rooms
Crooms = []

# array storing the list of logged in users
users = []

roomMsgs = dict()

# appends the default chat room
Crooms.append("Main")

@app.route("/")
def index():
    if session.get("username") == None:
        return redirect("/signin")
    user = session["username"]
    if session.get("current_room"):
        session.pop("current_room")
    return render_template("index.html", crooms=Crooms, handle=user)

@app.route("/signin", methods=['POST', 'GET'])
def signin():

    session.clear()

    if request.method == "POST":

        user = request.form.get("username")

        user = user.capitalize()

        if len(user) < 1 or user == "":
            return render_template("error.html", header="Error!", message="Invalid Username")
        elif user in users:
            return render_template("error.html", header="Error!", message="Username already exists")

        session["username"] = user

        session.permanent = True

        users.append(user)

        return redirect("/")

    return render_template("signin.html")

@app.route("/logout", methods=['POST', 'GET'])
def logout():

    person = session["username"]

    if person in users:
        users.remove(person)

    session.clear()

    return redirect("/")

@app.route("/room", methods=['POST', 'GET'])
def rooms():

    if request.method == "POST":

        input = request.form.get("input")

        input = input.capitalize()

        if len(input) < 1 or input == "":
            return render_template("error.html", header="Error!", message="Invalid Chat Room Name")
        elif input in Crooms:
            return render_template("error.html", header="Error!", message="Chat Room Already Exists")

        Crooms.append(input)

        return redirect(f"/room/{input}")

@app.route("/open", methods=['POST', 'GET'])
def open0():

    if request.method == "POST":
        page = request.form.get("pages")
        page = page.capitalize()

        session["current_room"] = page
        return redirect(f"/room/{page}")

@app.route("/room/<string:name>", methods=['POST', 'GET'])
def room(name):

    if len(name) < 1 or name == "":
        return render_template("error.html", header="Error!", message="Invalid Chat Room Name")

    name = name.capitalize()

    if name not in Crooms:
        Crooms.append(name)

    session["current_room"] = name

    session.permanent = True

    user = session["username"]

    if name in roomMsgs:
        messages = roomMsgs[name]
    else:
        roomMsgs[name] = []
        roomMsgs[name] = deque()
        messages = roomMsgs[name]

    if (len(roomMsgs[name]) > 100):
        roomMsgs[name].popleft()

    return render_template("room.html", handle=user, messages=messages)

@app.route("/error", methods=['POST', 'GET'])
def error():
    if session.get("username") == None:
        return redirect("/signin")

    return redirect("/")

@socketio.on("joined", namespace='/')
def join():

    room = session.get("current_room")

    join_room(room)

    emit("joined room", {'user': session["username"], 'room': room}, room=room)

@socketio.on("msg received")
def msg(data):
    msg0 = {'user': data["user0"],'content': data["content"],'date': data["date"],'time': data["time"]}
    msg1 = data["word"]
    room = session["current_room"]
    if room in roomMsgs:
        roomMsgs[room].append(msg0)
    else:
        roomMsgs[room] = []
        roomMsgs[room] = deque()
        roomMsgs[room].append(msg0)

    emit("msg display", {'msg': msg1}, room=room)

@socketio.on("left", namespace='/')
def left(data):

    room = session["current_room"]

    leave_room(room)

    emit("left room", data, room=room)

if __name__ == "__main__":
    app.run(debug=True)