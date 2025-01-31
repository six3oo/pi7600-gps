from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import threading
import cv2
import base64
import asyncio

app = FastAPI()


class VideoCaptureThread:
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
