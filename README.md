# EyeCU-Raspi
## Cmd for starting up the streaming server on Pi
```sudo uv4l -nopreview --auto-video_nr --driver raspicam --encoding mjpeg --width 640 --height 480 --framerate 2 --server-option '--port=9090' --server-option '--max-queued-connections=30' --server-option '--max-streams=25' --server-option '--max-threads=29'```
## The stream is available at the following address
```http://<RP IP address>:<specified port in the starting cmd>/stream/video.jpeg```
## Start the test code, run this command
```python pi_receiver.py```
## To see the live video feed
Once it starts, access localhost:5001 to see the live video feed.

You can find the entire instructions for harware and server setup below:

### Hardware include:
Raspberry Pi
Raspberry Pi Camera
Solenoid Lock
Relay

### Next, set up the Raspberry Pi: 

Use a monitor or a spare laptop for screen display for Raspberry Pi (RP). To connect RP to a screen, insert the HDMI cable on the RP board and insert the other end to your monitor. For this part, you’ll need to have an HDMI cable of your own. 
Set up a keyboard and mouse for your RP: Insert the USB cables on the provided keyboard and mouse to the USB hubs on RP. (There are 4 USB hubs on the RP so use any two of those 4 hubs).
Plug the power cable into the RP. I provided two power cables (1 for RP and the other for the Relay, use the one with the on/off button for the RP).
Turn on the power and wait for the RP OS to run and display on your monitor. Then there you are!

### Next, set up the Solenoid Lock and Relay:

Use the other power cable and plug it into the connector between the Solenoid lock and relay

We are now done with the hardware setup. Next, start the video streaming server on the RP desktop and run the driver code to get the RP to activate the Solenoid. 

Once you are on the desktop of the RP, try to connect it to your Wifi. Then check for the current IP address of the RP by mouse over the network icon or run “ifconfig” command on the terminal. Note down the IP address for later use.
Open Terminal -> cd Desktop -> python Lock_test.py -> You’ll see the lock is activated right after you run the file. Run localhost:5000/close on the browser in RP desktop to close the lock and localhost:5000/open to open it. 

*Important note: Don’t let the lock be open for too long, it will get hot and broken. So when moving on to the next steps, remember to return the lock to the normal state. 

To view or edit the code in Lock_test.py file, open the Python interface by clicking on the Raspberry icon on the top left most corner -> Programming -> Thonny Python IDE -> open the Lock_test.py file on Desktop.
To start the video streaming server, open Terminal, run these commands:
	
### Always run this command first: sudo pkill uv4l 
	
### Then run this command: 
	
sudo uv4l -nopreview --auto-video_nr --driver raspicam --encoding mjpeg --width 640 --height 480 --framerate 24 --server-option '--port=9090' --server-option '--max-queued-connections=30' --server-option '--max-streams=25' --server-option '--max-threads=29' 

*Note: You can manipulate the above command to adjust the framerate, width, height, etc.

### Keep the video streaming server and the driver code running on the RP desktop while starting the Face Recognition server on your main computer. Steps for running the FR server are below:

Download the code: pull the code from my Github repo in the following link: https://github.com/Vinguyen-32/EyeCU-Raspi
Open code in your IDE, to add more facial data, add more pictures in the folder “img”; the name of the picture will be the name of the user. To add more logic, modify the code on line 289 in the else if statement. The saved data are pulled from the pickle file if there is one existing on line 281.
Update the IP Address of the RP under rpi_address instance in the file pi_receiver.py. Save it and run python pi_receiver.py to start the server.
When the server starts, simply move the camera to your face, if the code recognizes you, the lock will open. After some seconds, which is defined in CLOSE_AFTER on line 193, the lock will automatically close. 
Once it starts, access localhost:5001 to see the live video feed.
