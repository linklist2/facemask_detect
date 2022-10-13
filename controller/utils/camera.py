import cv2
from .yolo_inference import inference


class VideoCamera(object):
    def __init__(self, net=None, camera_id=0):
        # 打开摄像头， 0代表笔记本内置摄像头
        self.cap = cv2.VideoCapture(camera_id)
        if not net:
            net = cv2.dnn.readNetFromONNX('models/yolov5n_mask.onnx')
            # net = cv2.dnn.readNetFromONNX('models/yolov5n_mask_pruned.onnx')

        self.net = net

    # 退出程序释放摄像头
    def __del__(self):
        self.cap.release()

    def get_frame(self):
        ret, frame = self.cap.read()
        if frame is None:
            return None
        frame = inference(frame, self.net, target_shape=(320, 320))

        if ret:
            ret, jpeg = cv2.imencode('.jpg', frame)
            return jpeg.tobytes()
