import RPi.GPIO as GPIO
import time
from time import sleep
from flask import Flask
appFlask = Flask(__name__)

servoPIN = 17
openAngle = 7
closeAngle = 1

GPIO.setmode(GPIO.BCM)
GPIO.setup(servoPIN, GPIO.OUT)

position = 0
p = GPIO.PWM(servoPIN, 50) # GPIO 17 for PWM with 50 Hz
p.start(position) # Initilization

@appFlask.route('/index')
def index():
    print ("dummy index")
    return '{"operation": "INDEX", "success": true}'

@appFlask.route('/open')
def open_servo():
    p.ChangeDutyCycle(openAngle)
    sleep(1)
    p.ChangeDutyCycle(0)
    return '{"operation": "OPEN", "success": true}'

@appFlask.route('/close' )
def close_servo():
    p.ChangeDutyCycle(closeAngle)
    sleep(1)
    p.ChangeDutyCycle(0)
    return '{"operation": "CLOSE", "success": true}'

if __name__ == "__main__":
    appFlask.run (debug=True, host='0.0.0.0', port="5000")
