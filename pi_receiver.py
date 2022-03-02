import cv2
import np
import face_recognition
import pickle
from os.path import exists
import requests
import threading
from flask import Response
from flask import Flask
import argparse
import os


app = Flask(__name__)

device_state = "CLOSE"

outputFrame = None
lock = threading.Lock()

rpi_address = "http://192.168.1.10"

# Hardcode raspberry pi streaming url for dev purpose. Move
# this to environment variable when used in production
cam = rpi_address + ":8080/stream/video.jpeg"

# Use cv2.CAP_ANY for auto select
# TODO: uncomment this for prod
# cap = cv2.VideoCapture(cam, cv2.CAP_ANY)

# Mock data from local video in case there is no RP
cap = cv2.VideoCapture("C:\\Users\\valer\\Downloads\\Video.mp4")

if not cap:
    print("!!! Failed VideoCapture: invalid parameter!")

known_face_encodings = []
known_face_names = []

# TODO: get all images from backend and encode here if pickle file is missing

# Server starts, all images are encoded and saved in a pickle file so when the server 
# starts again, all the encoded picture data are loaded from that pickle file.
if exists("./encodings.pickle") == True:
    f = open("./encodings.pickle", "rb")
    d = pickle.load(f)
    known_face_encodings = d["encodings"]
    known_face_names = d["names"]
    f.close()
# Assume there is a 'img' folder containing user's uploaded images, 
# do the following task to encode all the images in that directory and save to pickle file.
elif exists("./img") == True:
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

    data = {"encodings": known_face_encodings, "names": known_face_names}
    f = open("encodings.pickle", "wb")
    f.write(pickle.dumps(data))
    f.close()

# Handle processing live feed from RP. This will be run in a sub-thread 
def feed_receiver():
    global outputFrame, known_face_encodings, known_face_names, device_state

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
            
            # TODO: Server control the lock remotely
            # Make call to rPi
            # note: hard code for implementation purpose 
            if device_state == "CLOSE" and name == "Vi":
                # requests.get(rpi_address + ":5000/open")
                device_state = "OPEN"

            print("[Detect]: " + name)
         

        outputFrame = frame

        if cv2.waitKey(1) & 0xFF == ord('c'):
            print("closing lock")
            device_state = "CLOSE"
            # requests.get(rpi_address + ":5000/close")

# Generate output stream data
def generate():
	global outputFrame, lock
	while True:
		# Only perform when the lock is acquired
		with lock:
			if outputFrame is None:
				continue
			# encode the frame in JPG format
			(flag, encodedImage) = cv2.imencode(".jpg", outputFrame)
			# ensure the frame was successfully encoded
			if not flag:
				continue
		# Return output frame in the byte format
		yield(b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + bytearray(encodedImage) + b'\r\n')

# Endpoint to get the feed from recogniztion
@app.route("/video_feed")
def video_feed():
	return Response(generate(), mimetype = "multipart/x-mixed-replace; boundary=frame")



# Main thread
if __name__ == '__main__':
	# construct the argument parser and parse command line arguments
	ap = argparse.ArgumentParser()
	ap.add_argument("-o", "--port", type=int, default=8080)
	args = vars(ap.parse_args())

	# Run RP feed proccessor in a sub thread
	t = threading.Thread(target=feed_receiver)
	t.daemon = True
	t.start()

	# Run flask server
	app.run(host="0.0.0.0", port=args["port"], debug=True, threaded=True, use_reloader=False)

# release the resources
cap.release()
cv2.destroyAllWindows()
