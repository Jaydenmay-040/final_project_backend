import hmac
import sqlite3
import datetime

from flask import Flask, request
from flask_jwt import JWT, jwt_required, current_identity
from flask_cors import CORS
from flask_mail import Mail, Message

import cloudinary
import cloudinary.uploader
import DNS
import validate_email


class User(object):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password


def init_user_table():
    conn = sqlite3.connect('cloudiroid.db')
    print("Opened database successfully")

    conn.execute("CREATE TABLE IF NOT EXISTS user(user_id INTEGER PRIMARY KEY AUTOINCREMENT,"
                 "first_name TEXT NOT NULL,"
                 "last_name TEXT NOT NULL,"
                 "profile_img TEXT,"
                 "email TEXT NOT NULL,"
                 "username TEXT NOT NULL,"
                 "password TEXT NOT NULL)")
    print("user table created successfully")
    conn.close()


# Create product table
def init_post_table():
    conn = sqlite3.connect('cloudiroid.db')
    print("Opened database successfully")

    conn.execute("CREATE TABLE IF NOT EXISTS post("
                 "user_id"
                 "post_id INTEGER PRIMARY KEY AUTOINCREMENT,"
                 "post_img TEXT NOT NULL,"
                 "caption TEXT NOT NULL,"
                 "FOREIGN KEY (user_id) REFERENCES user(user_id))")

    print('post table created successfully')
    conn.close()


def init_comment_table():
    conn = sqlite3.connect('cloudiroid.db')
    print("Opened database successfully")

    conn.execute("CREATE TABLE IF NOT EXISTS comment("
                 "user_id,"
                 "post_id,"
                 "comment TEXT NOT NULL)")

    print('post table created successfully')
    conn.close()


def fetch_users():
    with sqlite3.connect('cloudiroid.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user")
        users = cursor.fetchall()

        new_data = []

        for data in users:
            new_data.append(User(data[0], data[4], data[5]))
    return new_data


def authenticate(username, password):
    users = fetch_users()
    username_table = {u.username: u for u in users}
    user = username_table.get(username, None)
    if user and hmac.compare_digest(user.password.encode('utf-8'), password.encode('utf-8')):
        return user


def identity(payload):
    users = fetch_users()
    userid_table = {u.id: u for u in users}
    user_id = payload['identity']
    return userid_table.get(user_id, None)


# Initialise app
app = Flask(__name__)
app.debug = True

app.config['SECRET_KEY'] = 'super-secret'
app.config['JWT_EXPIRATION_DELTA'] = datetime.timedelta(hours=24)   # Extending token expiration

# Mail config
app.config['MAIL_SERVER'] = "smtp.gmail.com"
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = "jmay41020@gmail.com"
app.config['MAIL_PASSWORD'] = "JM@y41020"
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True

# mail instantiation
mail = Mail(app)

jwt = JWT(app, authenticate, identity)

CORS(app)


@app.route('/protected')
@jwt_required()
def protected():
    return '%s' % current_identity