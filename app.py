from flask import Flask, render_template, request, url_for, redirect, make_response
import sqlite3
from sqlite3 import Error
import os
import uuid
from flask_cors import CORS, cross_origin
from flask_mail import Mail, Message

import sys


app = Flask(__name__)
conn = None

cors = CORS(app, resources={r"/*": {"origins": "*"}})
UPLOAD_FOLDER = 'images'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

# CORS(app)


def check_which_page(username: str):
    sqlfetch = """SELECT * from users WHERE name=?"""
    cur = conn.cursor()
    cur.execute(sqlfetch, (username,))
    rep = cur.fetchall()
    if rep[0].uuid == request.cookies.get("userID"):
        return redirect("/my_page")
    return redirect("/profile")


# TODO add better validation rules ?
def valid_password(password: str) -> bool:
    if len(password) < 8:
        return False
    if not any(char.isdigit() for char in password):
        return False
    if not any(char.isalpha() for char in password):
        return False
    return True


# TODO check email properly
def valid_email(email: str) -> bool:
    # if len(password) > 8:
    return True
    # return False


def valid_username(user: str) -> bool:
    # if len(password) > 8:
    sqlfetch = """SELECT * from users WHERE name=?"""
    cur = conn.cursor()
    cur.execute(sqlfetch, (user,))
    rep = cur.fetchall()
    if rep or len(user) < 1:
        # flash("This username is already taken")
        return False
    return True


def is_connected(uuid: str) -> bool:
    if uuid:
        print(uuid)
        sqlfetch = """SELECT * from users WHERE uuid=?"""
        cur = conn.cursor()
        cur.execute(sqlfetch, (uuid,))
        rep = cur.fetchall()
        if rep:
            return True
    return False

# @app.route('/upload')
# def upload_file1():
#    return render_template('upload.html')
	
# @app.route('/uploader', methods = ['GET', 'POST'])
# def upload_file2():
#    if request.method == 'POST':
#       f = request.files['file']
#       print("hello")
#     #   f.save(secure_filename(f.filename))
#       return 'file uploaded successfully'

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/uploader", methods=["POST"])
def upload():
    # print(request)
    print('This is error output', request, file=sys.stderr)
    print('This is standard output', file=sys.stdout)
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            # flash('No file part')
            print("error no file")
            return redirect(request.url)
        file = request.files['file']
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            print("error no selected file")
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = str(uuid.uuid4()) + "_" + file.filename
            # filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename.replace(" ", "_")))
            return redirect(url_for('download_file', name=filename))


@app.route("/404error")
def _404error():
    return render_template("404.html")


@app.route("/home")
def home():
    if not is_connected(request.cookies.get("userID")):
        return redirect("/404error")
    name = request.cookies.get("userID")
    # return '<h1>welcome ' + name + '</h1>'
    return render_template("home.html")


@app.route("/success_co")
def success_co():
    name = request.cookies.get("userID")
    return redirect("/home")
    # return redirect("/home.html")


# @app.route("/editor")
# def hello():
#     return render_template("index.html")


@app.route("/change_useremail", methods=["POST"])
def change_useremail():
    email = request.form["email"]
    uuid = request.cookies.get("userID")
    sqlup = """ UPDATE users SET email=? WHERE uuid=?"""
    cur = conn.cursor()
    cur.execute(sqlup, (email, uuid))
    conn.commit()


@app.route("/change_userpassword", methods=["POST"])
def change_userpassword():
    password = request.form["password"]
    # uuid = request.cookies.get("userID")
    sqlup = """ UPDATE users SET password=? WHERE uuid=?"""
    cur = conn.cursor()
    cur.execute(sqlup, (password, uuid))
    conn.commit()


@app.route("/change_username", methods=["GET, POST"])
def change_username():
    uuid = request.cookies.get("userID")
    if not is_connected(uuid):
        return redirect("/404error")
    if request.method == "POST":
        name = request.form["name"]
        sqlup = """ UPDATE users SET name=? WHERE uuid=?"""
        cur = conn.cursor()
        cur.execute(sqlup, (name, uuid))
        conn.commit()
        return render_template("my_page.html")
    return render_template("change_username.html")


@app.route("/my_page")
def my_page():
    uuid = request.cookies.get("userID")
    if not is_connected(uuid):
        return redirect("/404error")
    return render_template("my_page.html")


@app.route("/logout")
def logout():
    uuid = request.cookies.get("userID")
    if not is_connected(uuid):
        return redirect("/404error")
    sqlup = """ UPDATE users SET uuid=? WHERE uuid=?"""
    cur = conn.cursor()
    cur.execute(sqlup, (None, uuid))
    conn.commit()
    return render_template("index.html")


@cross_origin()
@app.route("/")
def hello():
    # if is_connected(request.cookies.get("userID"), ""):
    #     return redirect("/home")
    # return render_template("index.html")
    return render_template("index.html", is_logged="True")


# TODO error handling for signup


@cross_origin()
@app.route("/signup", methods=["POST", "GET"])
def signup():
    # if is_connected(request.cookies.get("userID"), ""):
    #     return redirect("/home")
    if request.method == "GET":
        return render_template("signup.html")
        # data = request.get_json().get("test")
    name = request.get_json().get("name")
    password = request.get_json().get("password")
    # email = request.get_json().get("email")
    # name = request.form["name"]
    # password = request.form["password"]
    # email = request.form["email"]
    print(request)
    print(name, password)
    if not (valid_password(password) and valid_email(email) and valid_username(name)):
        # flash("This username is already taken")
        return render_template("signup.html", error="error")
        # return dict("Error", "invalid something")
    # return jsonify({"status": "ko", "data": "fail"})
    conf_uuid = str(uuid.uuid4())
    sql = """ INSERT INTO users(name, email, password, confirmed, conf_uuid) VALUES(?,?,?,?,?) """
    # sql = """ INSERT INTO users(name, email, password) VALUES(?,?,?) """
    cur = conn.cursor()
    user = (name, email, password, False, conf_uuid)
    # user = (name, email, password)
    cur.execute(sql, user)
    conn.commit()
    # msg = Message(
    #     "Welcome to camagru",
    #     recipients=[email],
    #     html=render_template('email_conf_register.html', confirm_url="http://localhost:5000/" + conf_uuid),
    #     sender=app.config['MAIL_DEFAULT_SENDER']
    # )
    # mail.send(msg)
    # return (dict("Valid", True))
    # return jsonify({"status": "ok", "data": "ok"})
    return render_template("success_signup.html", email=email)
    # render_template("signup.html")


@app.route("/send_email", methods=["POST", "GET"])
def send_email():
    if request.method == "GET":
        return render_template("send_email.html")
    email = request.form["email"]
    print(request)
    if not valid_email(email):
        return render_template("send_email.html", error="error: invalid email")
    # msg = Message(
    #     "Welcome to camagru",
    #     recipients=[email],
    #     html=render_template('email_conf_register.html', confirm_url="http://localhost:5000/"),
    #     sender=app.config['MAIL_DEFAULT_SENDER']
    # )

    msg = Message()
    msg.subject = "Email Subject"
    msg.recipients = [email]
    # msg.sender = '42projectbdb@gmail.com'
    msg.sender = "percevallechat@yahoo.com"
    msg.body = "Email body"
    mail.send(msg)
    return render_template("success_signup.html", email=email)

@app.route("/webcam", methods=["POST", "GET"])
def show_webcam():
    return render_template("webcam.html")

@app.route("/login", methods=["POST", "GET"])
def login():
    # if is_connected(request.cookies.get("userID"), ""):
    #     return redirect("/home")
    if request.method == "POST":
        name = request.form["name"]
        password = request.form["password"]
        sqlfetch = """SELECT * from users WHERE name=? AND password=?"""
        cur = conn.cursor()
        cur.execute(sqlfetch, (name, password))
        rep = cur.fetchall()
        if not rep:
            return render_template("login.html")
        else:
            cookie = str(uuid.uuid4())
            print(cookie)
            sqlup = """ UPDATE users SET uuid=? WHERE name=?"""
            cur = conn.cursor()
            cur.execute(sqlup, (cookie, name))
            conn.commit()
            resp = make_response(redirect("/success_co"))
            resp.set_cookie("userID", cookie)
            return resp
            # return redirect("/success_co")
    return render_template("login.html")


if __name__ == "__main__":

    app.config["MAIL_SERVER"] = "smtp.gmail.com"
    app.config["MAIL_PORT"] = 465
    app.config["MAIL_USE_SSL"] = True
    # app.config['MAIL_USERNAME'] = "42projectbdb@gmail.com"
    # app.config['MAIL_PASSWORD'] = "bebeIvitch13/"
    app.config["MAIL_USERNAME"] = "percevallechat@yahoo.com"
    app.config["MAIL_PASSWORD"] = "Ivitch13/"
    mail = Mail(app)
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    app.config["CORS_HEADERS"] = "Content-Type"
    if not os.path.isfile("test.sqlite"):
        conn = sqlite3.connect("test.sqlite", check_same_thread=False)
        c = conn.cursor()
        # create_table_sql = """CREATE TABLE users (id int PRIMARY KEY,name text,email text, password text, uuid text, confirmed boolean, conf_uuid text)"""
        create_table_user_sql = """CREATE TABLE users (id int PRIMARY KEY,name text,email text, password text, uuid text)"""
        create_table_image_sql = """CREATE TABLE images (id int PRIMARY KEY,author text,address text, like_nbr int, comment_nbr int)"""
        c.execute(create_table_user_sql)
        conn.commit()
    else:
        conn = sqlite3.connect("test.sqlite", check_same_thread=False)
    app.run()
