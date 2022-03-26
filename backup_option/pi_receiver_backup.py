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


app = Flask(__name__)

DEBUG = True
MODE = "DETECT"

device_state = "CLOSE"

outputFrame = None
lock = threading.Lock()

# rpi_address = "http://192.168.1.10"
rpi_address = "http://172.20.224.113"

def handleTrain():
    print("Handle train")
def handleDetect():
    print("Handle detect")


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


# Handle processing live feed from RP 
def feed_receiver():
    global outputFrame, MODE, DEBUG, known_face_encodings, known_face_names, device_state

    while(True):
        # Capture frame-by-frame
        ret, frame = cap.read()
        if type(frame) == type(None):
            print("!!! Couldn't read frame!")
            break

        rgb_frame = frame[:, :, ::-1]
        face_locations = face_recognition.face_locations(rgb_frame)
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

        if MODE == "DETECT":
            handleDetect()
            for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
                matches = face_recognition.compare_faces(known_face_encodings, face_encoding)

                name = "Unknown"

                if len(known_face_encodings) > 0:
                    face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
                    best_match_index = np.argmin(face_distances)
                    if matches[best_match_index]:
                        name = known_face_names[best_match_index]
                
                if DEBUG:
                    # Draw a box around the face
                    cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)

                    # Draw a label with a name below the face
                    cv2.rectangle(frame, (left, bottom + 10), (right, bottom), (0, 0, 255), cv2.FILLED)
                    font = cv2.FONT_HERSHEY_DUPLEX
                    cv2.putText(frame, name, (left + 1, bottom + 6), font, 0.35, (255, 255, 255), 1)

                # Make call to rPi
                # note: hard code for implementation purpose 
                if device_state == "CLOSE" and name == "Vi":
                    # requests.get(rpi_address + ":5000/open")
                    device_state = "OPEN"

                print("[Detect]: " + name)
            
        elif MODE == "TRAIN":
            # handleTrain()
            print("Training")
            face_encoding = face_recognition.face_encodings(rgb_frame, face_locations)[0]

            # Create arrays of known face encodings and their names
            known_face_encodings.append(face_encoding)
            known_face_names = [
                "Vi"
            ]
            MODE = "DETECT"
        else:
            print("Unsupport mode: " + MODE)

        outputFrame = frame


        if cv2.waitKey(1) & 0xFF == ord('t'):
            MODE = "TRAIN"

        if cv2.waitKey(1) & 0xFF == ord('c'):
            print("closing lock")
            device_state = "CLOSE"
            # requests.get(rpi_address + ":5000/close")
        
        if cv2.waitKey(1) & 0xFF == ord('s'):
            print("Saving")
            data = {"encodings": known_face_encodings, "names": known_face_names}
            f = open("encodings.pickle", "wb")
            f.write(pickle.dumps(data))
            f.close()
        # Kill on key 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

def generate():
	# grab global references to the output frame and lock variables
	global outputFrame, lock
	# loop over frames from the output stream
	while True:
		# wait until the lock is acquired
		with lock:
			# check if the output frame is available, otherwise skip
			# the iteration of the loop
			if outputFrame is None:
				continue
			# encode the frame in JPEG format
			(flag, encodedImage) = cv2.imencode(".jpg", outputFrame)
			# ensure the frame was successfully encoded
			if not flag:
				continue
		# yield the output frame in the byte format
		yield(b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + 
			bytearray(encodedImage) + b'\r\n')


@app.route("/video_feed")
def video_feed():
	# return the response generated along with the specific media
	# type (mime type)
	return Response(generate(),
		mimetype = "multipart/x-mixed-replace; boundary=frame")



#  check to see if this is the main thread of execution
if __name__ == '__main__':
	# construct the argument parser and parse command line arguments
	ap = argparse.ArgumentParser()
	ap.add_argument("-i", "--ip", type=str, required=True,
		help="ip address of the device")
	ap.add_argument("-o", "--port", type=int, required=True,
		help="ephemeral port number of the server (1024 to 65535)")
	ap.add_argument("-f", "--frame-count", type=int, default=32,
		help="# of frames used to construct the background model")
	args = vars(ap.parse_args())
	# start a thread that will perform motion detection
	t = threading.Thread(target=feed_receiver)
	t.daemon = True
	t.start()
	# start the flask app
	app.run(host=args["ip"], port=args["port"], debug=True,
		threaded=True, use_reloader=False)

# feed_receiver()

# release the resources
cap.release()
cv2.destroyAllWindows()
