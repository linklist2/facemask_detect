# from flask_script import Manager
from controller import create_app
# 创建APP对象
app = create_app('dev')


if __name__ == '__main__':
    app.run(threaded=True, host="localhost")
