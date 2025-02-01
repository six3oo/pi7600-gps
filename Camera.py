from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import numpy as np
import threading
import cv2
import base64
import asyncio
from pi7600.Utils import SingletonMeta

app = FastAPI()


class VideoCaptureThread(metaclass=SingletonMeta):
    def __init__(self):
        self.cap = cv2.VideoCapture(-1, cv2.CAP_V4L2)
        self.running = True
        self.frame = None
        # self.queue = asyncio.Queue()  # Using asyncio.Queue for async-safe frame handling
        # self.thread = threading.Thread(target=self._reader)
        # self.thread.daemon = True
        # self.thread.start()

    def reader(self):
        #     loop = asyncio.new_event_loop()  # Create a new event loop in this thread
        #     asyncio.set_event_loop(loop)  # Set the new event loop as the current loop
        while self.running:
            # print(f'reading frame: {self.frame}')
            ret, frame = self.cap.read()
            if not ret:
                break
            _, buffer = cv2.imencode(".jpg", frame)
            if not _:
                continue
            frame_bytes = buffer.tobytes()
            self.frame = frame_bytes

    #         loop.run_until_complete(self.queue.put(frame))  # Run the async task in the new loop

    async def encode_frame_base64(self, frame) -> str:
        _, buffer = cv2.imencode(".jpg", frame)
        return base64.b64encode(buffer).decode("utf-8")

    # async def get_frame(self):
    # frame = await self.queue.get()
    # return await self.encode_frame_base64(frame)

    def release(self):
        self.running = False
        # self.cap.release()
        # self.thread.join()


class VideoStreamManager:
    def __init__(self):
        self.connections = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.connections.append(websocket)

    async def send_frame(self, frame):
        for websocket in self.connections:
            await websocket.send_bytes(frame)

    def disconnect(self, websocket: WebSocket):
        self.connections.remove(websocket)


class FacialRecognition:
    def __init__(self):
        self.cam = VideoCaptureThread()
        self.face_detect = cv2.CascadeClassifier(
            "./ml/haarcascade_frontalface_default.xml"
        )
        self.model = cv2.dnn.readNetFromONNX(
            "./ml/face_detection_yunet_2023mar_int8bq.onnx"
        )
        self.known_embeddings = {}
        self.known_faces = {"me": np.load("./ml/embeddings/me_embedding.npy")}

    def detect_face(self, image_path):
        img = cv2.imread(image_path)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = self.face_detect.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)

        if len(faces) > 0:
            (x, y, w, h) = faces[0]
            face_roi = img[y : y + h, x : x + w]
            return face_roi

    def preprocess_face(self, face_image):
        resized = cv2.resize(face_image, (224, 224))
        # image_float = resized.astype(np.float32) / 255.0
        image_uint8 = ((resized / np.max(resized)) * 255).astype("uint8")
        transposed = image_uint8.transpose(1, 0, 2)
        image_final = np.expand_dims(transposed, axis=0)
        return image_final

    def get_embedding(self, face_image):
        processed_face = self.preprocess_face(face_image)[0]
        bgr = cv2.cvtColor(processed_face, cv2.COLOR_RGB2BGR)
        blob = cv2.dnn.blobFromImage(bgr, swapRB=True)
        self.model.setInput(blob)
        embedding = self.model.forward()
        return embedding.flatten()

    def store_emeddings(self, face_image):
        if face_image is not None:
            embedding = self.get_embedding(face_image)
            self.known_embeddings["me"] = embedding
            np.save("me_embedding.npy", embedding)
        else:
            print("No face detected")

    def recognize_face(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_detect.detectMultiScale(gray, 1.1, 5)
        for x, y, w, h in faces:
            face_roi = frame[y : y + h, x : x + w]
            embedding = self.get_embedding(face_roi)
            identity = "Unknown"
            max_similarity = -1
            for name, known_embedding in self.known_faces.items():
                similarity = np.dot(embedding, known_embedding) / (
                    np.linalg.norm(embedding) * np.linalg.norm(known_embedding)
                )
                if similarity > max_similarity and similarity > 0.6:
                    max_similarity = similarity
                    identity = name

            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(
                frame,
                identity,
                (x, y - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.9,
                (0, 255, 0),
                2,
            )
            return frame


# face_test = FacialRecognition()
# front = face_test.detect_face("/home/daze/images/front.jpg")
# face_test.store_emeddings(front)
