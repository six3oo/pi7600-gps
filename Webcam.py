import cv2
import base64


class SingletonMeta(type):
    """
    This metaclass ensures that only one instance of any class using it exists.
    """

    _instances = {}  # Dictionary to hold single instances

    def __call__(cls, *args, **kwargs):
        """
        If an instance of cls doesn't exist, create one and store it in _instances.
        Otherwise, return the existing instance.
        """
        if cls not in cls._instances:
            # print(f"Creating new instance of {cls.__name__}")
            cls._instances[cls] = super(SingletonMeta, cls).__call__(*args, **kwargs)
        else:
            # print(f"Using existing instance of {cls.__name__}")
            pass
        return cls._instances[cls]


class Webcam(metaclass=SingletonMeta):
    def __init__(self):
        self.cap = cv2.VideoCapture(0)


    def encode_frame(self, frame):
        _, buffer = cv2.imencode('.jpg', frame)
        return base64.b64encode(buffer).decode('utf-8')

