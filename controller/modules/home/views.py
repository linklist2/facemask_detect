from flask import session, render_template, redirect, url_for, Response
from controller.modules.home import home_blu
from controller.utils.camera import VideoCamera
import pygame.camera

video_camera = None
global_frame = None
global_id = 0

# 获取摄像头数量
pygame.camera.init()
camera_nums = len(pygame.camera.list_cameras())


# 主页
@home_blu.route('/')
def index():
    # 模板渲染
    username = session.get("username")
    ambient = round(28.88, 1)  # (sensor.get_ambient(),1) 室内温度
    temp = round(36.55, 1)  # (sensor.get_object_1(),1) 体温
    tempInfo = {
        'ambient': ambient,
        'temp': temp
    }
    # bus.close()

    if not username:
        return redirect(url_for("user.login"))
    return render_template("index.html", **tempInfo)


@home_blu.route('/change_camera')
def change_camera():
    global video_camera
    global global_id
    video_camera.__del__()
    global_id += 1

    video_camera = VideoCamera(global_id % camera_nums)
    return redirect(url_for("home.index"))


# 获取视频流
def video_stream():
    global video_camera
    global global_frame

    if video_camera is None:
        video_camera = VideoCamera()

    while True:
        frame = video_camera.get_frame()
        if frame is not None:
            global_frame = frame
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')
        else:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + global_frame + b'\r\n\r\n')


# 视频流
@home_blu.route('/video_viewer')
def video_viewer():
    # 模板渲染
    username = session.get("username")
    # voice_alert()
    if not username:
        return redirect(url_for("user.login"))
    return Response(video_stream(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')
