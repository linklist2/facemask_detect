from flask import session, redirect, url_for, request, render_template

from controller.modules.user import user_blu
from controller.modules.home import close_camera


# 登录
@user_blu.route("/login", methods=["GET", "POST"])
def login():
    username = session.get("username")

    if username:
        return redirect(url_for("home.index"))

    if request.method == "GET":
        return render_template("login.html")
    # 获取参数
    username = request.form.get("username")
    password = request.form.get("password")
    # 校验参数
    if not all([username, password]):
        return render_template("login.html", errmsg="参数不足")

    # 校验对应的管理员用户数据
    if username == "admin" and password == "admin":
        # 验证通过
        session["username"] = username
        return redirect(url_for("home.index"))

    return render_template("login.html", errmsg="用户名或密码错误")


# 退出登录
@user_blu.route("/logout")
def logout():
    # 删除session数据
    session.pop("username", None)
    close_camera()
    # 返回登录页面
    return redirect(url_for("user.login"))
