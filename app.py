from flask import Flask, render_template, request, url_for, redirect, make_response
import sqlite3
from sqlite3 import Error
import os
import base64
import uuid
from flask_cors import CORS, cross_origin
from flask_mail import Mail, Message

import sys


app = Flask(__name__, static_url_path="/images/", static_folder="images/")
conn = None

cors = CORS(app, resources={r"/*": {"origins": "*"}})
UPLOAD_FOLDER = "images"
ALLOWED_EXTENSIONS = {"txt", "pdf", "png", "jpg", "jpeg", "gif"}

CORS(app)

# TODO NOT FINISHED
def get_all_comments(image: str):
    cur = conn.cursor()
    sqlfetch = """SELECT * from comments WHERE address=?"""
    cur.execute(sqlfetch, (image,))
    image_ = cur.fetchall()


# TAKES image adress and username of current user
def add_comment(image: str, user: str, txt: str):
    cur = conn.cursor()
    sqlfetch = """SELECT id from users WHERE name=?"""
    cur.execute(sqlfetch, (user,))
    user_ = cur.fetchone()
    sqlfetch = """SELECT id from images WHERE address=?"""
    cur.execute(sqlfetch, (image,))
    image_ = cur.fetchone()
    sql = """ INSERT INTO comments(content, image_, user_) VALUES(?,?,?) """
    cur.execute(sql, (txt, image_[0], user_[0]))
    conn.commit()


def is_image_liked(image: str, user: str) -> bool:
    cur = conn.cursor()
    sqlfetch = """SELECT id from users WHERE name=?"""
    cur.execute(sqlfetch, (user,))
    user_ = cur.fetchone()
    sqlfetch = """SELECT id from images WHERE address=?"""
    cur.execute(sqlfetch, (image,))
    image_ = cur.fetchone()
    sql = """ SELECT * FROM likes WHERE user_id=? AND image_id=? """
    cur.execute(sql, (image_[0], user_[0]))
    resp = cur.fetchall()
    if not resp:
        return False
    return True


def get_all_likes(image: str) -> int:
    cur = conn.cursor()
    sqlfetch = """SELECT * from likes WHERE address=?"""
    cur.execute(sqlfetch, (image,))
    image_ = cur.fetchall()
    return len(image_)


# TAKES image adress and username of current user
def remove_like(image: str, user: str):
    cur = conn.cursor()
    sqlfetch = """SELECT id from users WHERE name=?"""
    cur.execute(sqlfetch, (user,))
    user_ = cur.fetchone()
    sqlfetch = """SELECT id from images WHERE address=?"""
    cur.execute(sqlfetch, (image,))
    image_ = cur.fetchone()
    sqlfetch = """DELETE * from likes WHERE user_id=? AND image_id=?"""
    cur.execute(
        sqlfetch,
        (
            user_[0],
            image_[0],
        ),
    )
    conn.commit()


# TAKES image adress and username of current user
def add_like(image: str, user: str):
    cur = conn.cursor()
    sqlfetch = """SELECT id from users WHERE name=?"""
    cur.execute(sqlfetch, (user,))
    user_ = cur.fetchone()
    sqlfetch = """SELECT id from images WHERE address=?"""
    cur.execute(sqlfetch, (image,))
    image_ = cur.fetchone()
    sql = """ INSERT INTO likes(image_, user_) VALUES(?,?) """
    like_ = (image_[0], user_[0])
    cur.execute(sql, like_)
    conn.commit()


def get_images(index: int):
    cur = conn.cursor()
    sql = "SELECT * FROM images ORDER BY created"
    cur.execute(sql)
    res = cur.fetchall()
    true_index = index * 5
    i = 0
    ret = []
    while i < len(res) and i < true_index + 5:
        print(i, res[i], res[i][2])
        ret.append(res[i][2])
        i += 1
    return ret


# @cross_origin()
@app.route("/send_webcam", methods=["POST"])
def send_webcam():
    image_data = request.get_json()["image"]
    # Save the image to a file or perform any other desired operations
    # Example: saving the image to a file named 'image.jpg'
    with open("image.png", "wb") as file:
        file.write(base64.b64decode(image_data.split(",")[1]))
    return {"message": "Image uploaded successfully"}


# @app.route("/get_image", methods=["POST, GET"])
# def get_image():
# #   data = request.data
# #   display(data.decode("utf-8"))
# #   return ''
#     # if request.method == "GET":
#         # return render_template("webcam.html")
#     # elif request.method == "POST":
#     print("lol")
#     data = request.get_data()
#     with open("loltest.jpg", 'wb') as f:
#         f.write(data)
# return ''


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
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/uploader", methods=["POST"])
def upload():
    # print(request)
    print("This is error output", request, file=sys.stderr)
    print("This is standard output", file=sys.stdout)
    if request.method == "POST":
        # check if the post request has the file part
        if "file" not in request.files:
            # flash('No file part')
            print("error no file")
            return redirect(request.url)
        file = request.files["file"]
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == "":
            print("error no selected file")
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = str(uuid.uuid4()) + "_" + file.filename
            # filename = secure_filename(file.filename)
            file.save(
                os.path.join(app.config["UPLOAD_FOLDER"], filename.replace(" ", "_"))
            )
            return redirect(url_for("download_file", name=filename))


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
    return render_template(
        "homepage.html",
        is_logged=str(is_connected(request.cookies.get("userID"))),
        images=get_images(0),
    )


# TODO error handling for signup


@cross_origin()
@app.route("/signup", methods=["POST", "GET"])
def signup():
    if is_connected(request.cookies.get("userID")) == "True":
        return redirect("/")
    if request.method == "GET":
        return render_template("signup.html", error="")
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
            # create_table_sql = """CREATE TABLE users (id int PRIMARY KEY,name text,email text, password text, uuid text, confirmed boolean, conf_uuid text)"""

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
    app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
    app.config["CORS_HEADERS"] = "Content-Type"
    if not os.path.isfile("basedatatest.sqlite"):
        conn = sqlite3.connect("basedatatest.sqlite", check_same_thread=False)
        c = conn.cursor()
        # create_table_sql = """CREATE TABLE users (id int PRIMARY KEY,name text,email text, password text, uuid text, confirmed boolean, conf_uuid text)"""
        create_table_user_sql = """CREATE TABLE users (user_id integer PRIMARY KEY, name text,email text, password text, uuid text)"""
        create_table_image_sql = """CREATE TABLE images (image_id integer PRIMARY KEY, created datetime default current_timestamp, address text, like_nbr int, comment_nbr int, user_id int, FOREIGN KEY(user_id) REFERENCES users(user_id))"""
        create_table_comment_sql = """CREATE TABLE comments (comment_id integer PRIMARY KEY, created datetime default current_timestamp, content text, image_id int, user_id int, FOREIGN KEY(image_id) REFERENCES images(image_id), FOREIGN KEY(user_id) REFERENCES users(user_id))"""
        create_table_like_sql = """CREATE TABLE likes (like_id integer PRIMARY KEY, image_id int, user_id int, FOREIGN KEY(image_id) REFERENCES images(image_id), FOREIGN KEY(user_id) REFERENCES users(user_id))"""
        c.execute(create_table_user_sql)
        c.execute(create_table_image_sql)
        c.execute(create_table_comment_sql)
        c.execute(create_table_like_sql)
        conn.commit()
        sql = """ INSERT INTO users(name) VALUES(?) """
        c.execute(sql, ("toto",))
        conn.commit()
        sql = """ INSERT INTO images(address, user_id, like_nbr, comment_nbr) VALUES(?,?,?,?) """
        c.execute(sql, ("images/cat.png", 1, 0, 0))
        conn.commit()
    else:
        conn = sqlite3.connect("basedatatest.sqlite", check_same_thread=False)
    app.run()
