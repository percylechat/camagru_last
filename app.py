from flask import Flask, render_template, request, url_for, redirect, make_response
import sqlite3
from sqlite3 import Error
import os
import base64
import sys
import uuid
import re

from PIL import Image
from flask_cors import CORS, cross_origin
from flask_mail import Mail, Message
import bcrypt




app = Flask(__name__, static_url_path="/images/", static_folder="images/")
# conn = None

cors = CORS(app, resources={r"/*": {"origins": "*"}})
UPLOAD_FOLDER = "images"
ALLOWED_EXTENSIONS = {"txt", "pdf", "png", "jpg", "jpeg", "gif"}
app.config["MAIL_SERVER"] = "mail.gandi.net"
app.config["MAIL_PORT"] = 465
app.config["MAIL_USE_SSL"] = True
app.config["MAIL_USERNAME"] = "camagru@greatparis.fr"
app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PWD")
mail = Mail(app)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["CORS_HEADERS"] = "Content-Type"
salt = bcrypt.gensalt()
CORS(app)


def get_img_id(image: str) -> int:
    cur = conn.cursor()
    sqlfetch = """SELECT image_id from images WHERE address=?"""
    cur.execute(sqlfetch, (image,))
    ids = cur.fetchall()
    return ids[0][0]


def get_user_name(user_id):
    cur = conn.cursor()
    sqlfetch = """SELECT name from users WHERE user_id=?"""
    cur.execute(sqlfetch, (user_id,))
    name = cur.fetchone()
    return name[0]

def get_user_id(uuid):
    cur = conn.cursor()
    sqlfetch = """SELECT user_id from users WHERE cookie_uuid=?"""
    cur.execute(sqlfetch, (uuid,))
    name = cur.fetchone()
    return name[0]


def get_all_comments(image: str):
    cur = conn.cursor()
    id_ = get_img_id(image)
    sqlfetch = """SELECT * from comments WHERE image_id=? ORDER BY created"""
    cur.execute(sqlfetch, (id_,))
    comments_ = cur.fetchall()
    t_comment = []
    eleme = ()
    for el in comments_:
        user_ = get_user_name(el[4])
        eleme += (el[2],)
        eleme += (user_,)
        eleme += (el[1],)
        t_comment.append(eleme)
        eleme = ()
    return t_comment


def is_image_liked(image: str, user: str) -> bool:
    cur = conn.cursor()
    sqlfetch = """SELECT user_id from users WHERE cookie_uuid=?"""
    cur.execute(sqlfetch, (user,))
    user_ = cur.fetchone()
    sqlfetch = """SELECT image_id from images WHERE address=?"""
    cur.execute(sqlfetch, (image,))
    image_ = cur.fetchone()
    sql = """ SELECT * FROM likes WHERE user_id=? AND image_id=? """
    cur.execute(
        sql,
        (
            user_[0],
            image_[0],
        ),
    )
    resp = cur.fetchone()
    print(resp)
    if resp is None:
        return False
    return True


def get_all_likes(image: str) -> int:
    cur = conn.cursor()
    sqlfetch = """SELECT * from likes WHERE address=?"""
    cur.execute(sqlfetch, (image,))
    image_ = cur.fetchall()
    return len(image_)


def get_images_and_infos(index: int, user: str):
    cur = conn.cursor()
    sql = "SELECT * FROM images ORDER BY created"
    cur.execute(sql)
    res = cur.fetchall()
    true_index = index * 5
    i = 0
    ret_i = []
    ret_l = []
    ret_c = []
    ret_il = []
    while i < len(res) and i < true_index + 5:
        ret_i.append(res[i][2])
        ret_l.append(res[i][3])
        ret_c.append(get_all_comments(res[i][2]))
        ret_il.append(is_image_liked(res[i][2], user))
        i += 1
    return ret_i, ret_l, ret_c, ret_il


def get_images(index: int):
    cur = conn.cursor()
    sql = "SELECT * FROM images ORDER BY created"
    cur.execute(sql)
    res = cur.fetchall()
    true_index = index * 5
    i = true_index
    ret = []
    while i < len(res) and i < true_index + 5:
        ret.append(res[i][2])
        i += 1
    return ret


def get_images_for_user(id_: int):
    cur = conn.cursor()
    sql = "SELECT address FROM images WHERE user_id=? ORDER BY created"
    print(id_)
    cur.execute(sql, (id_,))
    res = cur.fetchall()
    i = 0
    ret = []
    print(res)
    while i < len(res):
        ret.append("images/"+str(res[i][0])+".png")
        i += 1
    return ret


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


def sanitize_input(txt: str) -> str:
    if "delete" in txt.lower():
        return "Forbidden word"
    if "select" in txt.lower():
        return "Forbidden word"
    if "drop" in txt.lower():
        return "Forbidden word"
    if "insert" in txt.lower():
        return "Forbidden word"
    if "update" in txt.lower():
        return "Forbidden word"
    return "ok"


def valid_password(password: str) -> bool:
    if len(password) < 8:
        return "Password is too short"
    if not any(char.isdigit() for char in password):
        return "Missing digit in password"
    if not any(char.isalpha() for char in password):
        return "Missing letter in password"
    return "ok"


def valid_email(email: str) -> bool:
    if "@" not in email or len(email) < 6:
        return "error in email"
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    if not re.match(pattern, email):
        return "error in email"
    return "ok"


def valid_username(user: str) -> str:
    sqlfetch = """SELECT * from users WHERE name=?"""
    cur = conn.cursor()
    cur.execute(sqlfetch, (user,))
    rep = cur.fetchall()
    if rep or len(user) < 1:
        return "This username is already taken"
    return "ok"


def is_connected(uuid_: str) -> bool:
    if uuid_:
        sqlfetch = """SELECT * from users WHERE cookie_uuid=?"""
        cur = conn.cursor()
        cur.execute(sqlfetch, (uuid_,))
        rep = cur.fetchall()
        if rep:
            return True
    return False


def get_email_is_true(uuid):
    sqlfetch = """SELECT * from users WHERE cookie_uuid=?"""
    cur = conn.cursor()
    cur.execute(sqlfetch, (uuid,))
    rep = cur.fetchone()
    return rep[7]


def send_email_comment(user_id: int):
    sqlfetch = """SELECT * from users WHERE user_id=?"""
    cur = conn.cursor()
    cur.execute(sqlfetch, (user_id,))
    rep = cur.fetchone()
    if rep[7] == True:
        msg = Message(
            "Camagru news",
            recipients=[rep[2]],
            html=render_template("email_comment.html"),
            sender="camagru@greatparis.fr",
        )
        mail.send(msg)


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


@app.route("/delete_image", methods=["POST"])
def delete_image():
    user = request.cookies.get("userID")
    address = request.form["image"]
    cur = conn.cursor()
    sql = "DELETE FROM images WHERE address=?"
    cur.execute(sql, (address,))
    conn.commit()
    return redirect("/webcam")


@app.route("/remove_like", methods=["POST"])
def remove_like():
    user = request.cookies.get("userID")
    image = request.form["image"]
    print(image)
    cur = conn.cursor()
    sqlfetch = """SELECT user_id from users WHERE cookie_uuid=?"""
    cur.execute(sqlfetch, (user,))
    user_ = cur.fetchone()
    sqlfetch = """SELECT image_id from images WHERE address=?"""
    cur.execute(sqlfetch, (image,))
    image_ = cur.fetchone()
    sqlfetch = """DELETE FROM likes WHERE user_id=? AND image_id=?"""
    cur.execute(
        sqlfetch,
        (
            user_[0],
            image_[0],
        ),
    )
    conn.commit()
    sqlfetch = """SELECT like_nbr from images WHERE address=?"""
    cur.execute(sqlfetch, (image,))
    like_n_ = cur.fetchone()
    print("add like", like_n_)
    new_like = like_n_[0] - 1
    print(new_like)
    sql = """ UPDATE images SET like_nbr=? WHERE address=?"""
    cur.execute(
        sql,
        (
            new_like,
            image,
        ),
    )
    conn.commit()
    return redirect("/")


@app.route("/add_like", methods=["POST"])
def add_like():
    user = request.cookies.get("userID")
    image = request.form["image"]
    cur = conn.cursor()
    print(image)
    sqlfetch = """SELECT user_id from users WHERE cookie_uuid=?"""
    cur.execute(sqlfetch, (user,))
    user_ = cur.fetchone()
    sqlfetch = """SELECT image_id from images WHERE address=?"""
    cur.execute(sqlfetch, (image,))
    image_ = cur.fetchone()
    sql = """ INSERT INTO likes(image_id, user_id) VALUES(?,?) """
    like_ = (image_[0], user_[0])
    cur.execute(sql, like_)
    sqlfetch = """SELECT like_nbr from images WHERE address=?"""
    cur.execute(sqlfetch, (image,))
    like_n_ = cur.fetchone()
    print("add like", like_n_)
    new_like = like_n_[0] + 1
    print(new_like)
    sql = """ UPDATE images SET like_nbr=? WHERE address=?"""
    cur.execute(
        sql,
        (
            new_like,
            image,
        ),
    )
    conn.commit()
    return redirect("/")


@app.route("/add_comment", methods=["POST"])
def add_comment():
    user = request.cookies.get("userID")
    image = request.form["image"]
    txt = request.form["comment"]
    cur = conn.cursor()
    sqlfetch = """SELECT user_id from users WHERE cookie_uuid=?"""
    cur.execute(sqlfetch, (user,))
    user_ = cur.fetchone()
    sqlfetch = """SELECT image_id from images WHERE address=?"""
    cur.execute(sqlfetch, (image,))
    image_ = cur.fetchone()
    sql = """ INSERT INTO comments(content, image_id, user_id) VALUES(?,?,?) """
    cur.execute(sql, (txt, image_[0], user_[0]))
    conn.commit()
    send_email_comment(user_[0])
    return redirect("/")


#TODO add 3rd image
@app.route("/webcam", methods=["POST", "GET"])
def show_webcam():
    uuid_ = request.cookies.get("userID")
    if not is_connected(uuid_):
        return redirect("/404error")
    return render_template("webcam.html", infos=get_images_for_user(get_user_id(uuid_)))


def merge_image(img_name, image_filter, uuid_):
    id_ = get_user_id(uuid_)
    name_end = "images/"+str(uuid.uuid4())+".png"
    image_base = Image.open(img_name)
    image_on = Image.open(image_filter)
    if image_base.size != image_on.size:
        print("Les dimensions des images ne correspondent pas.")
    image_on = image_on.convert("RGBA")
    image_end = Image.alpha_composite(image_base.convert("RGBA"), image_on)
    image_end.save(name_end)
    c = conn.cursor()
    sql = """ INSERT INTO images(address, user_id, like_nbr) VALUES(?,?,?) """
    c.execute(sql, (name_end, id_, 0))
    conn.commit()

@app.route("/send_webcam", methods=["POST"])
def send_webcam():
    image_data = request.get_json()["image"]
    image_filter = request.get_json()["filter"]
    uuid_ = request.cookies.get("userID")
    name = str(uuid.uuid4())
    img_name = "images/" + name + ".png"
    with open(img_name, "wb") as file:
        file.write(base64.b64decode(image_data.split(",")[1]))
    merge_image(img_name, image_filter, uuid_)
    return {"message": "Image uploaded successfully"}


@app.route("/uploader", methods=["POST"])
def upload():
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
    return render_template("images/404.html")


@app.route("/success_co")
def success_co():
    name = request.cookies.get("userID")
    return redirect("/")
    # return redirect("/home.html")


@cross_origin()
@app.route("/change_preference", methods=["POST"])
def change_pref():
    uuid_ = request.cookies.get("userID")
    if not is_connected(uuid_):
        return redirect("/404error")
    pref = request.form["pref_email"]
    if pref is True:
        pref = False
    else:
        pref = True
    sqlup = """ UPDATE users SET is_email=? WHERE cookie_uuid=?"""
    cur = conn.cursor()
    cur.execute(sqlup, (pref, uuid_))
    conn.commit()
    return render_template("my_page.html", pref_email=pref)


@cross_origin()
@app.route("/change_useremail", methods=["POST", "GET"])
def change_email():
    uuid_ = request.cookies.get("userID")
    if not is_connected(uuid_):
        return redirect("/404error")
    if request.method == "GET":
        return render_template("change_useremail.html", error="")
    if request.method == "POST":
        name = request.form["n_name"]
        check = sanitize_input(name)
        if check != "ok":
            return render_template("change_useremail.html", error=check)
        check = valid_email(name)
        if check != "ok":
            return render_template("change_useremail.html", error=check)
        sqlup = """ UPDATE users SET email=? WHERE cookie_uuid=?"""
        cur = conn.cursor()
        cur.execute(sqlup, (name, uuid_))
        conn.commit()
        return render_template("my_page.html", pref_email=get_email_is_true(uuid_))
    return render_template("change_useremail.html", error="")


@cross_origin()
@app.route("/change_userpassword", methods=["POST", "GET"])
def change_password():
    uuid_ = request.cookies.get("userID")
    if not is_connected(uuid_):
        return redirect("/404error")
    if request.method == "GET":
        return render_template("change_userpassword.html", error="")
    if request.method == "POST":
        name = request.form["n_name"]
        check = sanitize_input(name)
        if check != "ok":
            return render_template("change_userpassword.html", error=check)
        check = valid_password(name)
        if check != "ok":
            return render_template("change_userpassword.html", error=check)
        bytes_ = name.encode('utf-8')
        hash_ = bcrypt.hashpw(bytes_, salt)
        sqlup = """ UPDATE users SET password=? WHERE cookie_uuid=?"""
        cur = conn.cursor()
        cur.execute(sqlup, (hash_, uuid_))
        conn.commit()
        return render_template("my_page.html", pref_email=get_email_is_true(uuid_))
    return render_template("change_userpassword.html", error="")


@cross_origin()
@app.route("/change_username", methods=["POST", "GET"])
def change_name():
    uuid_ = request.cookies.get("userID")
    if not is_connected(uuid_):
        return redirect("/404error")
    if request.method == "GET":
        return render_template("change_username.html", error="")
    if request.method == "POST":
        name = request.form["n_name"]
        check = sanitize_input(name)
        if check != "ok":
            return render_template("change_username.html", error=check)
        check = valid_username(name)
        if check != "ok":
            return render_template("change_username.html", error=check)
        sqlup = """ UPDATE users SET name=? WHERE cookie_uuid=?"""
        cur = conn.cursor()
        cur.execute(sqlup, (name, uuid_))
        conn.commit()
        return render_template("my_page.html", pref_email=get_email_is_true(uuid_))
    return render_template("change_username.html", error="")


#TODO ensure routes when connected or not
@app.route("/profile")
def my_page():
    uuid_ = request.cookies.get("userID")
    if not is_connected(uuid_):
        return redirect("/404error")
    return render_template("my_page.html", pref_email=get_email_is_true(uuid_))


@app.route("/logout")
def logout():
    uuid_ = request.cookies.get("userID")
    if not is_connected(uuid_):
        return redirect("/404error")
    sqlup = """ UPDATE users SET cookie_uuid=? WHERE cookie_uuid=?"""
    cur = conn.cursor()
    cur.execute(sqlup, (None, uuid_))
    conn.commit()
    return redirect("/")


@cross_origin()
@app.route("/")
def hello(index: int = 0):
    index = request.args.get("index")
    if index is None or int(index) < 0:
        index = 0
    print(index, type(index))
    if not is_connected(request.cookies.get("userID")):
        images = get_images(int(index))
        likes, comments, is_likeds = [], [], []
        for i in images:
            likes.append(None)
            comments.append([])
            is_likeds.append(False)
        ret = zip(images, likes, comments, is_likeds)
    else:
        images_, likes, comments, is_likeds = get_images_and_infos(
            int(index), request.cookies.get("userID")
        )
        ret = zip(images_, likes, comments, is_likeds)
    return render_template(
        "homepage.html",
        is_logged=str(is_connected(request.cookies.get("userID"))),
        infos=ret,
        index=str(int(index))
    )


@app.route("/conf_email/<uuid_>")
def confirm_inscription(uuid_: str):
    sqlfetch = """SELECT * from users WHERE conf_uuid=?"""
    cur = conn.cursor()
    cur.execute(sqlfetch, (uuid_,))
    rep = cur.fetchone()
    if not rep:
        return render_template("homepage.html", is_logged="false", images=get_images(0))
    else:
        cookie = str(uuid.uuid4())
        sqlup = """ UPDATE users SET confirmed=?, cookie_uuid=? WHERE conf_uuid=?"""
        cur = conn.cursor()
        cur.execute(sqlup, (True, cookie, uuid_))
        conn.commit()
        resp = make_response(redirect("/success_co"))
        resp.set_cookie("userID", cookie)
        return resp


@cross_origin()
@app.route("/signup", methods=["POST", "GET"])
def signup():
    if is_connected(request.cookies.get("userID")) == "True":
        return redirect("/")
    if request.method == "GET":
        return render_template("signup.html", error="")
    name = request.form["n_name"]
    password = request.form["n_password"]
    email = request.form["n_email"]
    check = sanitize_input(name)
    if check != "ok":
        return render_template("signup.html", error=check)
    check = valid_username(name)
    if check != "ok":
        return render_template("signup.html", error=check)
    check = sanitize_input(password)
    if check != "ok":
        return render_template("signup.html", error=check)
    check = valid_password(password)
    if check != "ok":
        return render_template("signup.html", error=check)
    check = sanitize_input(email)
    if check != "ok":
        return render_template("signup.html", error=check)
    check = valid_email(email)
    if check != "ok":
        return render_template("signup.html", error=check)
    conf_uuid = str(uuid.uuid4())
    bytes_ = password.encode('utf-8')
    hash_ = bcrypt.hashpw(bytes_, salt)
    sql = """ INSERT INTO users(name, email, password, confirmed, conf_uuid, is_email) VALUES(?,?,?,?,?,?) """
    # sql = """ INSERT INTO users(name, email, password) VALUES(?,?,?) """
    cur = conn.cursor()
    cur.execute(
        sql,
        (name, email, hash_, False, conf_uuid, True),
    )
    conn.commit()
    msg = Message(
        "Welcome to camagru",
        recipients=[email],
        html=render_template(
            "email_conf_register.html",
            confirm_url="http://localhost:5000/conf_email/" + conf_uuid,
        ),
        sender="camagru@greatparis.fr",
    )
    mail.send(msg)
    return render_template("success_signup.html", email=email)


@app.route("/reset_password", methods=["POST"])
def reset_password():
    name = request.form["name"]
    sqlfetch = """SELECT email from users WHERE name=?"""
    cur = conn.cursor()
    cur.execute(sqlfetch, (name,))
    email = cur.fetchone()
    if email[0] is None:
        return render_template("login.html", error="This user does not exist")
    new_pass = str(uuid.uuid4())
    bytes_ = new_pass.encode('utf-8')
    hash_ = bcrypt.hashpw(bytes_, salt)
    sqlup = """ UPDATE users SET password=? WHERE name=?"""
    cur = conn.cursor()
    cur.execute(sqlup, (hash_, name))
    conn.commit()
    print(email, email[0])
    msg = Message(
        "Camagru",
        recipients=[email[0]],
        html=render_template(
            "email_reset_password.html",
            new_password=new_pass,
        ),
        sender="camagru@greatparis.fr",
    )
    mail.send(msg)
    return render_template("reset_email_template.html")


@app.route("/login", methods=["POST", "GET"])
def login():
    if is_connected(request.cookies.get("userID")):
        return redirect("/")
    if request.method == "POST":
        name = request.form["name"]
        password = request.form["password"]
        sqlfetch = """SELECT * from users WHERE name=?"""
        cur = conn.cursor()
        cur.execute(sqlfetch, (name,))
        rep = cur.fetchone()
        if rep is None:
            return render_template("login.html", error="This user does not exist")
        userBytes = password.encode('utf-8')
        result = bcrypt.checkpw(userBytes, rep[3])
        if result is False:
            return render_template("login.html", error="Wrong password")
        else:
            cookie = str(uuid.uuid4())
            sqlup = """ UPDATE users SET cookie_uuid=? WHERE name=?"""
            cur = conn.cursor()
            cur.execute(sqlup, (cookie, name))
            conn.commit()
            resp = make_response(redirect("/success_co"))
            resp.set_cookie("userID", cookie)
            return resp
            # create_table_sql = """CREATE TABLE users (id int PRIMARY KEY,name text,email text, password text, uuid text, confirmed boolean, conf_uuid text)"""

            # return redirect("/success_co")
    return render_template("login.html", error="")


print("toto", file=sys.stderr)
if __name__ == "__main__":
    global conn

    print("hello", file=sys.stderr)
    if not os.path.isfile("basedatatest.sqlite"):
        print("here", file=sys.stderr)
        conn = sqlite3.connect("basedatatest.sqlite", check_same_thread=False)
        c = conn.cursor()
        create_table_user_sql = """CREATE TABLE users (user_id INTEGER PRIMARY KEY AUTOINCREMENT,name text,email text, password text, cookie_uuid text, confirmed boolean, conf_uuid text, is_email boolean)"""
        # create_table_user_sql = """CREATE TABLE users (user_id integer PRIMARY KEY, name text,email text, password text, uuid text)"""
        create_table_image_sql = """CREATE TABLE images (image_id INTEGER PRIMARY KEY AUTOINCREMENT, created datetime default current_timestamp, address text, like_nbr int, user_id int, FOREIGN KEY(user_id) REFERENCES users(user_id))"""
        create_table_comment_sql = """CREATE TABLE comments (comment_id INTEGER PRIMARY KEY AUTOINCREMENT, created datetime default current_timestamp, content text, image_id int, user_id int, FOREIGN KEY(image_id) REFERENCES images(image_id), FOREIGN KEY(user_id) REFERENCES users(user_id))"""
        create_table_like_sql = """CREATE TABLE likes (like_id INTEGER PRIMARY KEY AUTOINCREMENT, image_id int, user_id int, FOREIGN KEY(image_id) REFERENCES images(image_id), FOREIGN KEY(user_id) REFERENCES users(user_id))"""
        c.execute(create_table_user_sql)
        c.execute(create_table_image_sql)
        c.execute(create_table_comment_sql)
        c.execute(create_table_like_sql)
        conn.commit()
        # sql = """ INSERT INTO users(name, email, password, confirmed, is_email) VALUES(?,?,?,?,?) """
        # c.execute(sql, ("toto","percevallechat@gmail.com", "xx", True, True))
        # conn.commit()
        # sql = """ INSERT INTO images(address, user_id, like_nbr) VALUES(?,?,?) """
        # c.execute(sql, ("images/cat.png", 1, 0))
        # conn.commit()
    else:
        print("there", file=sys.stderr)
        conn = sqlite3.connect("basedatatest.sqlite", check_same_thread=False)
    app.run(host="0.0.0.0", port=5000)
