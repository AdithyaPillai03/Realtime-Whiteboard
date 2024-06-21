from flask import Flask, render_template, request, session, redirect, url_for
from flask_socketio import SocketIO, join_room, leave_room, send, emit
import random
import string
import os
from dotenv import load_dotenv, dotenv_values 

# loading variables from .env file
load_dotenv()

key = os.getenv("SECRET_KEY")

app = Flask(__name__)
app.config['SECRET_KEY'] = key
socketio = SocketIO(app)

rooms = {}


def generate_unique_code(length):
    while True:
        code = ""
        for _ in range(length):
            code += random.choice(string.digits)
        if code not in rooms:
            break
    return code


@app.route('/',methods=["GET","POST"])
def root():
    session.clear()
    if request.method == "POST":
        name = request.form.get("name")
        code = request.form.get("code")
        join = request.form.get("join",False)
        create = request.form.get("create",False)

        if not name:
            return render_template("home.html",error="Please enter a name",code=code,name=name)
        if join != False and not code:
            return render_template("home.html",error="Please enter a room code!",code=code,name=name)

        room = code

        if create != False:
            room = generate_unique_code(4)
            rooms[room] = {"members":0}
        elif code not in rooms:
            return render_template("home.html",error="Room does not exist!",code=code,name=name)
        

        session["room"] = room
        session["name"] = name
        return redirect(url_for("room"))
        
    return render_template("home.html")


@app.route('/room')
def room():
    room = session.get("room")
    print(rooms)
    if room is None or session.get("name") is None or room not in rooms:
        return redirect(url_for("root"))

    return render_template("room.html",code=room)



@socketio.on("connect")
def connect(auth):
    room = session.get("room")
    name = session.get("name")
    if not room or not name:
        return
    if room not in rooms:
        leave_room(room)
        return

    join_room(room)
    send({"name":name,"message":" has entered the room"},to=room)
    rooms[room]["members"] += 1
    print(name,"has joined the room with code",  room)
    print("---------------------------------------------------------------------------------")
    print("list of room players are",rooms)

@socketio.on("startDrawing")
def drawing(data):
    room = session.get("room")
    if not room or not room in rooms:
        return
    emit("startDrawing",data,broadcast=True)


@socketio.on("drawing")
def drawing(data):
    room = session.get("room")
    if not room or not room in rooms:
        return
    emit("drawing",data,broadcast=True)
    

@socketio.on("disconnect")
def disconnect():
    room = session.get("room")
    name = session.get("name")
    leave_room(room)

    if room in rooms:
        rooms[room]["members"] -= 1
        if rooms[room]["members"] <= 0:
            del rooms[room]
    
    send({"name": name, "message": "has left the room"}, to=room)
    print("#####################################################################################")
    print(f"{name} has left the room {room}")



if __name__ == '__main__':
    socketio.run(app)
