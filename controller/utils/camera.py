import cv2
from .yolo_inference import inference

class VideoCamera(object):
    def __init__(self, camera_id=0):
        # 打开摄像头， 0代表笔记本内置摄像头
        self.cap = cv2.VideoCapture(camera_id)

    # 退出程序释放摄像头
    def __del__(self):
        self.cap.release()

    def get_frame(self):
        ret, frame = self.cap.read()
        if frame is None:
            return None
        frame = inference(frame, target_shape=(320, 320))

        if ret:
            ret, jpeg = cv2.imencode('.jpg', frame)
            return jpeg.tobytes()



