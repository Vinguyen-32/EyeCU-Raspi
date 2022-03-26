from flask_socketio import SocketIO
from flask import Flask, render_template, request
import socketio
import pickle
import face_recognition
import cv2
import numpy as np
import base64

from os.path import exists
import requests
import threading
from flask import Response
from flask import Flask
import argparse
import os
import time

device_state = "CLOSE"
open_timestamp = None
CLOSE_AFTER = 8

def convert_byte_to_mat(byte):
    nparr = np.frombuffer(byte, np.byte)
    img2 = cv2.imdecode(nparr, cv2.IMREAD_ANYCOLOR)
    return img2

def convert_mat_to_byte(mat):
    frame = cv2.imencode('.jpg', mat)[1].tobytes()
    return frame



# here we are experimenting with the face recog
justin_image = face_recognition.load_image_file('./img/vi.jpg')
justin_face_encoding = face_recognition.face_encodings(justin_image)[0]
known_face_encodings = [
    justin_face_encoding
]
known_face_names = [
    "Vi Nguyen"
]



app = Flask(__name__)
#, ping_timeout=60, ping_interval=10''
socketio = SocketIO(app,cors_allowed_origins="*",  logger=True, engineio_logger=True)
socketio = SocketIO(app,cors_allowed_origins="*", async_mode="threading")

@app.route('/test')
def test():
    return "test"

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect', namespace='/web')
def connect_web():
    print('[INFO] Web client connected: {}'.format(request.sid))


@socketio.on('disconnect', namespace='/web')
def disconnect_web():
    print('[INFO] Web client disconnected: {}'.format(request.sid))


@socketio.on('connect', namespace='/cv')
def connect_cv():
    print('[INFO] CV client connected: {}'.format(request.sid))
    
@socketio.on('pingpong', namespace='/cv')
def pingpong(): # this indicates that the client is ready to send data
    print('ping pong')
    socketio.emit("send_data", room=request.sid, namespace="/cv")

@socketio.on('disconnect', namespace='/cv')
def disconnect_cv():
    print('[INFO] CV client disconnected: {}'.format(request.sid))


outputFrame = None
lock = threading.Lock()

rpi_address = "http://192.168.1.23"

# Hardcode raspberry pi streaming url for dev purpose. Move
# this to environment variable when used in production
cam = rpi_address + ":8080/stream/video.jpeg"

# Use cv2.CAP_ANY for auto select
# TODO: uncomment this for prod
cap = cv2.VideoCapture(cam, cv2.CAP_ANY)

# Mock data from local video in case there is no RP
# cap = cv2.VideoCapture("C:\\Users\\valer\\Downloads\\Video.mp4")

if not cap:
    print("!!! Failed VideoCapture: invalid parameter!")

known_face_encodings = []
known_face_names = []

# TODO: get all images from backend and encode here if pickle file is missing

# Server starts, all images are encoded and saved in a pickle file so when the server 
# starts again, all the encoded picture data are loaded from that pickle file.
if exists("./encodings.pickle") == True:
    print("Found pickle file")
    f = open("./encodings.pickle", "rb")
    d = pickle.load(f)
    known_face_encodings = d["encodings"]
    known_face_names = d["names"]
    f.close()
    print("Done importing from pickle file")
# Assume there is a 'img' folder containing user's uploaded images, 
# do the following task to encode all the images in that directory and save to pickle file.
elif exists("./img") == True:
    print("Found img folder")
    directory = os.fsencode("./img")
    
    for file in os.listdir(directory):
        filename = os.fsdecode(file)
        if filename.endswith(".jpg"): 
            print(filename)
            image = face_recognition.load_image_file("./img/" + filename)
            face_encoding = face_recognition.face_encodings(image)[0]

            # Create arrays of known face encodings and their names
            known_face_encodings.append(face_encoding)
            known_face_names.append(filename.replace(".jpg", ""))
            continue
        else:
            continue
    print("Import from img folder")

    data = {"encodings": known_face_encodings, "names": known_face_names}
    f = open("encodings.pickle", "wb")
    f.write(pickle.dumps(data))
    f.close()

def feed_receiver():
    global outputFrame, known_face_encodings, known_face_names, device_state, open_timestamp, CLOSE_AFTER

    while(True):
        # Capture frame-by-frame
        ret, frame = cap.read()
        if type(frame) == type(None):
            print("!!! Couldn't read frame!")
            break
        
        rgb_frame = frame[:, :, ::-1]
        face_locations = face_recognition.face_locations(rgb_frame)
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
            
        for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
            matches = face_recognition.compare_faces(known_face_encodings, face_encoding)

            name = "Unknown"

            if len(known_face_encodings) > 0:
                face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
                best_match_index = np.argmin(face_distances)
                if matches[best_match_index]:
                    name = known_face_names[best_match_index]
            
            
            # Draw a box around the face
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)

            # Draw a label with a name below the face
            cv2.rectangle(frame, (left, bottom + 10), (right, bottom), (0, 0, 255), cv2.FILLED)
            font = cv2.FONT_HERSHEY_DUPLEX
            cv2.putText(frame, name, (left + 1, bottom + 6), font, 0.35, (255, 255, 255), 1)
        
            if device_state == "CLOSE" and name != "Unknown":
                print("Detected: " + name)
                device_state = "OPEN"
                open_timestamp = time.time()
                requests.get(rpi_address + ":5000/open")

        frame = cv2.imencode('.jpg', frame)[1].tobytes()
        frame = base64.encodebytes(frame).decode("utf-8")
        socketio.emit('server2web', {'image':"data:image/jpeg;base64,{}".format(frame)}, namespace='/web')

        if device_state == "OPEN" and open_timestamp and time.time() - open_timestamp > CLOSE_AFTER:
            device_state = "CLOSE"
            open_timestamp = None
            requests.get(rpi_address + ":5000/close")

if __name__ == "__main__":

    # Run RP feed proccessor in a sub thread
    t = threading.Thread(target=feed_receiver)
    t.daemon = True
    t.start()

    print('[INFO] Starting server at http://localhost:5001')
    socketio.run(app=app, host='localhost', port=5001)