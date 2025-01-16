import cv2
import base64

class Webcam:
    def __init__(self):
        pass


    def encode_frame(self, frame):
        _, buffer = cv2.imencode('.jpg', frame)
        return base64.b64encode(buffer).decode('utf-8')



