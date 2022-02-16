import time
from time import sleep
from flask import Flask
appFlask = Flask(__name__)

@appFlask.route('/index')
def index():
    print ("dummy index")
    return '{"operation": "INDEX", "success": true}'

@appFlask.route('/open')
def open_servo():
    return '{"operation": "OPEN", "success": true}'

@appFlask.route('/close' )
def close_servo():
    return '{"operation": "CLOSE", "success": true}'

if __name__ == "__main__":
    appFlask.run (debug=True, host='0.0.0.0', port="5000")
