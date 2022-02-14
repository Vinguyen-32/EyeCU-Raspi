import cv2
import np
import face_recognition
import pickle
from os.path import exists


DEBUG = True
MODE = "DETECT"

def handleTrain():
    print("Handle train")
def handleDetect():
    print("Handle detect")


# Hardcode raspberry pi streaming url for dev purpose. Move
# this to environment variable when used in production
cam = "http://192.168.1.10:8080/stream/video.jpeg"

# Use cv2.CAP_ANY for auto select
cap = cv2.VideoCapture(cam, cv2.CAP_ANY)

if not cap:
    print("!!! Failed VideoCapture: invalid parameter!")

known_face_encodings = []
known_face_names = []

if exists("./encodings.pickle") == True:
    f = open("./encodings.pickle", "rb")
    d = pickle.load(f)
    known_face_encodings = d["encodings"]
    known_face_names = d["names"]
    f.close()


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

            print("[Detect]: " + name)
        
    elif MODE == "TRAIN":
        # handleTrain()
        print("Training")
        face_encoding = face_recognition.face_encodings(rgb_frame, face_locations)[0]

        # Create arrays of known face encodings and their names
        known_face_encodings.append(face_encoding)
        known_face_names = [
            "Hieu", "Vi", "Ki"
        ]
        MODE = "DETECT"
    else:
        print("Unsupport mode: " + MODE)

    # Display the resulting frame
    if DEBUG:
        cv2.imshow('frame',frame)

    if cv2.waitKey(1) & 0xFF == ord('t'):
        MODE = "TRAIN"
    
    if cv2.waitKey(1) & 0xFF == ord('s'):
        print("Saving")
        data = {"encodings": known_face_encodings, "names": known_face_names}
        f = open("encodings.pickle", "wb")
        f.write(pickle.dumps(data))
        f.close()
    # Kill on key 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# release the resources
cap.release()
cv2.destroyAllWindows()
