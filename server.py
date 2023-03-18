from flask import Flask, request, redirect
from threading import Thread
from flask_cors import CORS
import os
import json
import socket
import platform
from flask_socketio import SocketIO

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
CORS(app)
socketio = SocketIO(app, allowed_cors_origins = "*")

app.config['CONFIG'] = {}

print("[SERVER] [LOADING CONFIG FILE]")
def update_config():
    with open(os.path.expanduser(r'~\Documents\OneLinkData\config.json'), 'r') as f:
        app.config['CONFIG'] = json.load(f)

def save_config(config):
    with open(os.path.expanduser(r'~\Documents\OneLinkData\config.json'), 'w') as json_file:
        json.dump(config, json_file, indent=4)

try:
    update_config()
except Exception as e:
    print(e)
    exit()

print("[SERVER] [SUCCESSFULLY LOADED CONFIG FILE]")

def shutdown_server():
    #func = request.environ.get('werkzeug.server.shutdown')
    #if func is None:
    #    raise RuntimeError('Not running with the Werkzeug Server')
    #func()
    print("== STOPPING SERVER == ")
    socketio.stop()
    
@app.get('/shutdown')
def shutdown():
    shutdown_server()
    return {"status": "Shutting down.."}

@app.route("/")
def index():
    return redirect('/ping')

@app.route("/ping")
def ping():
    update_config()
    os = platform.system()
    if os == "Darwin":
        os = "MacOS"
    return {"host_id": app.config['CONFIG'].get("HOST_ID"), "host_name": socket.gethostname(), "os": os}

@app.route("/set_host", methods=['POST'])
def setHost():
    app.config['CONFIG']['HOST_ID'] = request.form['id']
    app.config['CONFIG']['HOST_PASSWORD'] = request.form['password']
    save_config(app.config['CONFIG'])
    return {'status': "OK"}


def run():
    print("[SERVER] STARTING SERVER!")
    socketio.run(app, port=21452)
    #app.run(port=21452)


def keep_alive():
    t = Thread(target=run)
    t.start()

if __name__ == "__main__":
    run()
