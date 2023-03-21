import socketio
import os
import subprocess
import time
import psutil
import ctypes, sys
import socket
import json
import platform
import base64
from io import BytesIO
from example import example_config, example_startup_task
import webbrowser
from PIL import Image

from multiprocessing import Process
#from PIL import Image
#from __future__ import print_function
import pyautogui
#from pyvda import AppView, get_apps_by_z_order, VirtualDesktop, get_virtual_desktops
 
p = None
saved_image = None
mouse_image = Image.open('mouse.png')
mouse_image.thumbnail((25, 25))

def screenshot_screen(locked):
    if not locked:
        global saved_image
        image = pyautogui.screenshot()
        image.paste(mouse_image, pyautogui.position(), mouse_image)
        x, y = image.size
        if x > 50 and y > 50:
            image = image.resize((round(x / 3), round(y / 3)))
        #image.save("screenshot.jpg")2
        image_bytes = BytesIO()
        image.save(image_bytes, format='PNG')
        image_bytes = image_bytes.getvalue()
        img_str = base64.b64encode(image_bytes)
        #image_bytes = image_bytes.getvalue()
        #buffered = BytesIO()
        #image.save(buffered, format="JPEG")
        #img_str = base64.b64encode(buffered.getvalue())
        #with open("screenshot.jpg", "rb") as f:
        #    img_str = base64.b64encode(f.read())
        saved_image = img_str

operating_system = platform.system()
if operating_system == "Windows":
    from pyvda import AppView, get_apps_by_z_order, VirtualDesktop, get_virtual_desktops

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

sio = socketio.Client()

print("[LOADING CONFIG FILE]")

config = {}

if not os.path.isfile(os.path.expanduser(r'~\Documents\OneLinkData\config.json')):
    with open(os.path.expanduser(r'~\Documents\OneLinkData\config.json'), 'w') as json_file:
        json.dump(example_config, json_file, indent=4)

if not os.path.isfile(r'~\Documents\OneLinkData\OneLinkStartUpTask.xml') and operating_system == "Windows":
    with open(os.path.expanduser(r'~\Documents\OneLinkData\OneLinkStartUpTask.xml'), 'w') as xml_file:
        #json.dump(example_startup_task, xml_file, indent=4)
        xml_file.write(example_startup_task)
        #os.system("cd\ \ncacls c:/windows/tasks /T /E /P Administrators:F \ncacls c:/windows/tasks /T /E /P SYSTEM:F")

try:
    with open(os.path.expanduser(r'~\Documents\OneLinkData\config.json'), 'r') as f:
        config = json.load(f)
except Exception as e:
    print(e)
    exit()

if not config.get("HOST_ID") and operating_system == "Windows":
    if is_admin():
        os.system(f"SCHTASKS /Create /XML {os.path.expanduser('~/Documents/OneLinkData/OneLinkStartUpTask.xml')} /TN OneLinkStartup /F")   
    else:
        # Re-run the program with admin rights
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        exit()
    pass

print("[SUCCESSFULLY LOADED CONFIG FILE]")

def saveChanges(config):
    with open(os.path.expanduser(r'~\Documents\OneLinkData\config.json'), 'w') as json_file:
        json.dump(config, json_file, indent=4)

@sio.event
def connect():
    print("[SERVER CONNECTED!]")
    if not config.get('HOST_ID'):
        webbrowser.open('http://link.pop-plays.live/configure')
        sio.disconnect()
        #while True: 
        #    success = False
        #    password = input("[CHOOSE A PASSWORD] >>> ")
        #    while True:
        #        confirmPassword = input("[CONFIRM PASSWORD] >>> ")
        #        if confirmPassword.lower() == 'back':
        #            break
        #        if password != confirmPassword:
        #            print("PASSWORDS DO NOT MATCH. TRY AGAIN (back to reset password)")
        #        else:
        #            success = True
        #            os = platform.system()
        #            if os == "Darwin":
        #                os = "MacOS"
        #            sio.emit("createHost", {'password': password, 'os': os})
        #            break
        #    if success:
        #        break
        #print("[CREATING HOST ACCOUNT...]")
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
            os = platform.system()
            cpu = psutil.cpu_percent()
            mem =  psutil.virtual_memory()[2]
            locked = False
            if os == 'Windows':
                for proc in psutil.process_iter():
                    if(proc.name() == "LogonUI.exe"):
                        locked = True
            fdesktops = []
            if os == 'Windows':
                for desktop in get_virtual_desktops():
                    #if desktop.id == VirtualDesktop.current().id:
                    payload = {
                        #'id': desktop.id,
                        'name': desktop.name,
                        "active": desktop.id == VirtualDesktop.current().id
                    }
                    fdesktops.append(payload)
            sio.emit('computerUpdate', {'cpu': cpu, 'mem': mem, 'locked': locked, 'desktops': fdesktops, 'id': config['HOST_ID'], 'os': os, 'image': saved_image})
            screenshot_screen(locked)
            #print("[INFO] HEARTBEAT SENT!")
            time.sleep(0.5)
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
        #os.system('python3 lock.py')
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
        sio.emit('evaluated', {"content": data.get('content'), 'id': config['HOST_ID'], 'result': result})
    except Exception as e:
        print(str(e))
        sio.emit('evaluated', {"content": data.get('content'), 'id': config['HOST_ID'], 'result': str(e), 'error': True})



print("[ATTEMPTING TO CONNECT..]")
from server import keep_alive
keep_alive()
p = Process(target=sio.connect(config['SERVER_URL'], wait_timeout = 10))
p.run()

#p.join()
#sio.wait()

