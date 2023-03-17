import socketio
import os
import subprocess
import time
import psutil
import socket
import json
import platform

#from __future__ import print_function
import pyautogui
#from pyvda import AppView, get_apps_by_z_order, VirtualDesktop, get_virtual_desktops
 


sio = socketio.Client()

config = {}
with open('config.json', 'r') as f:
  config = json.load(f)

def saveChanges(config):
    with open('config.json', 'w') as json_file:
        json.dump(config, json_file, indent=4)

@sio.event
def connect():
    print("[SERVER CONNECTED!]")
    if not config['HOST_ID']:
        while True: 
            success = False
            password = input("[CHOOSE A PASSWORD] >>> ")
            while True:
                confirmPassword = input("[CONFIRM PASSWORD] >>> ")
                if confirmPassword.lower() == 'back':
                    break
                if password != confirmPassword:
                    print("PASSWORDS DO NOT MATCH. TRY AGAIN (back to reset password)")
                else:
                    success = True
                    os = platform.system()
                    if os == "Darwin":
                        os = "MacOS"
                    sio.emit("createHost", {'password': password, 'os': os})
                    break
            if success:
                break
        print("[CREATING HOST ACCOUNT...]")
    else:
        print("[LOGGING IN TO SERVER]")
        sio.emit('login', {'type': 'HOST', 'id': config['HOST_ID'], "password": config['HOST_PASSWORD'], 'name': socket.gethostname()})

@sio.event
def createdHost(data):
    config['HOST_ID'] = data.get("id")
    config['HOST_PASSWORD'] = data.get("password")
    saveChanges(config)
    sio.emit('login', {'type': 'HOST', 'id': config['HOST_ID'], "password": config['HOST_PASSWORD'], 'name': socket.gethostname()})
    print("[HOST CREATED! LOGGING IN..]")
@sio.event
def connect_error(data):
    print("[CONNECTION TO SERVER FAILED. RETRYING]")

@sio.event
def disconnect():
    print("[DISCONNECTED FROM SERVER. RETRYING]")

@sio.event
def loggedIn(data):
    if data['status'] == 'OK':
        print("[HOST CONNECTION ESTABLISHED]")
        #pyautogui.alert(text='This computer is currently connected to the [HOST] network. Normal user privileges are given.', title='Connection Established', button='OK')
        while True:
            cpu = psutil.cpu_percent()
            mem =  psutil.virtual_memory()[2]
            locked = False
            fdesktops = []
            sio.emit('computerUpdate', {'cpu': cpu, 'mem': mem, 'locked': locked, 'desktops': fdesktops})
            time.sleep(3)
    else:
        print("[LOGIN FAILED!]")
        return
@sio.event
def evaluate(data):
    mousePos = pyautogui.position()
    def moveLeft(px):
        res = mousePos[0] - px
        if res > 0:
            pyautogui.moveTo(res, mousePos[1], 0.5)
    def moveRight(px):
        res = mousePos[0] + px
        if res < pyautogui.size()[0]:
            pyautogui.moveTo(res, mousePos[1], 0.5)
    def moveUp(px):
        res = mousePos[1] - px
        if res > 0:
            pyautogui.moveTo(mousePos[0], res, 0.5)
    def moveDown(px):
        res = mousePos[1] + px
        if res < pyautogui.size()[1]:
            pyautogui.moveTo(mousePos[0], res, 0.5)
    def lock_device():
        #switchDesktop('Lockscreen')
        os.system('python3 lock.py')
        #while True:
        #    record = False
        #    for x in pyautogui.getAllWindows():  
        #        if x.title == "LOGIN UI":
        #            record = True
        #    if record:
        #        break
        #    time.sleep(0.5)
        #pyautogui.hotkey('win', 'ctrl', 't')
        #pyautogui.click()'
        pass
    try:
        result = eval(data.get('content'))
        #print(result)
        sio.emit('evaluated', {"content": data.get('content'), 'result': result})
    except Exception as e:
        print(str(e))
        sio.emit('evaluated', {"content": data.get('content'), 'result': str(e), 'error': True})


sio.connect(config['SERVER_URL'], wait_timeout = 10)
sio.wait()

print("[HOST SHUT DOWN WRITING CONFIG CHANGES]")
with open('config.json', 'w') as json_file:
  json.dump(config, json_file, indent=4)
print()
print("CHANGES WRITTEN")