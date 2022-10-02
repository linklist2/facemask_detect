import cv2
from .yolo_inference import inference

class VideoCamera(object):
    def __init__(self):
        # 打开摄像头， 0代表笔记本内置摄像头
        self.cap = cv2.VideoCapture(0)

    # 退出程序释放摄像头
    def __del__(self):
        self.cap.release()

    def get_frame(self):
        ret, frame = self.cap.read()
        frame = inference(frame, target_shape=(320, 320))

        if ret:
            ret, jpeg = cv2.imencode('.jpg', frame)
            return jpeg.tobytes()
