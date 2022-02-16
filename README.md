# EyeCU-Raspi
## Cmd for starting up the streaming server on Pi
```sudo uv4l -nopreview --auto-video_nr --driver raspicam --encoding mjpeg --width 640 --height 480 --framerate 2 --server-option '--port=9090' --server-option '--max-queued-connections=30' --server-option '--max-streams=25' --server-option '--max-threads=29'```
## The stream is available at the following address
```http://<RP IP address>:<specified port in the starting cmd>/stream/video.jpeg```
## Start the test code, run this command
```python pi_receiver.py```
