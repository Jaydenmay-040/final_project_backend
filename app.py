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
                 "bio TEXT,"
                 "email TEXT UNIQUE NOT NULL,"
                 "username TEXT UNIQUE NOT NULL,"
                 "password TEXT NOT NULL)")
    print("user table created successfully")
    conn.close()


# Create product table
def init_post_table():
    conn = sqlite3.connect('cloudiroid.db')
    print("Opened database successfully")

    conn.execute("CREATE TABLE IF NOT EXISTS post("
                 "user_id INTEGER,"
                 "username,"
                 "post_id INTEGER PRIMARY KEY AUTOINCREMENT,"
                 "profile_img TEXT,"
                 "words TEXT NOT NULL,"
                 "FOREIGN KEY (username) REFERENCES user(username),"
                 "FOREIGN KEY (user_id) REFERENCES user(user_id))")

    print('post table created successfully')
    conn.close()


def init_comment_table():
    conn = sqlite3.connect('cloudiroid.db')
    print("Opened database successfully")

    conn.execute("CREATE TABLE IF NOT EXISTS comment("
                 "comment_id INTEGER PRIMARY KEY AUTOINCREMENT,"
                 "user_id,"
                 "username,"
                 "post_id,"
                 "comment TEXT NOT NULL,"
                 "seen BOOLEAN NOT NULL,"
                 "FOREIGN KEY (user_id) REFERENCES user(user_id),"
                 "FOREIGN KEY (username) REFERENCES user(username),"
                 "FOREIGN KEY (post_id) REFERENCES post(post_id))")

    print('post table created successfully')
    conn.close()


def init_like_table():
    conn = sqlite3.connect('cloudiroid.db')
    print('opened database successfully')

    conn.execute("CREATE TABLE IF NOT EXISTS like("
                 "user_id,"
                 "post_id,"
                 "seen BOOLEAN NOT NULL,"
                 "FOREIGN KEY (user_id) REFERENCES user(user_id),"
                 "FOREIGN KEY (post_id) REFERENCES post(post_id))")
    print('like table create successfully')
    conn.close()


def init_follow_table():
    conn = sqlite3.connect('cloudiroid.db')
    print("opened database successfully")

    conn.execute("CREATE TABLE IF NOT EXISTS follow("
                 "follower INTEGER,"
                 "followed INTEGER,"
                 "seen BOOLEAN NOT NULL,"
                 "FOREIGN KEY (follower) REFERENCES user(user_id),"
                 "FOREIGN KEY (followed) REFERENCES user(user_id))")

    print('table successfully created')

    conn.close()


def init_dm_table():
    conn = sqlite3.connect('cloudiroid.db')
    conn.execute("CREATE TABLE IF NOT EXISTS dm("
                 "dm_id INTEGER PRIMARY KEY AUTOINCREMENT,"
                 "message TEXT NOT NULL,"
                 "sender_id,"
                 "sender_username,"
                 "receiver_id,"
                 "receiver_username,"
                 "seen BOOLEAN NOT NULL,"
                 "FOREIGN KEY (sender_id) REFERENCES user(user_id),"
                 "FOREIGN KEY (sender_username) REFERENCES user(username),"
                 "FOREIGN KEY (receiver_id) REFERENCES user(user_id),"
                 "FOREIGN KEY (receiver_username) REFERENCES user(username))")

    print("dm Table created successfully")


init_user_table()
init_post_table()
init_comment_table()
init_like_table()
init_follow_table()
init_dm_table()


def fetch_users():
    with sqlite3.connect('cloudiroid.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user")
        users = cursor.fetchall()

        new_data = []

        for data in users:
            new_data.append(User(data[0], data[6], data[7]))
    return new_data


users = fetch_users()
username_table = {u.username: u for u in users}
userid_table = {u.id: u for u in users}


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
app.config['JWT_EXPIRATION_DELTA'] = datetime.timedelta(hours=24)  # Extending token expiration

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


class Database(object):
    def __init__(self):
        self.conn = sqlite3.connect('cloudiroid.db')
        self.conn.row_factory = self.dict_factory
        self.cursor = self.conn.cursor()

    def dict_factory(self, cursor, row):
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]
        return d

    def register(self, first_name, last_name, email, username, password):
        # cloudinary.config(cloud_name='ddvdj4vy6', api_key='416417923523248',
        #                   api_secret='v_bGoSt-EgCYGO2wIkFKRERvqZ0')
        # upload_result = None
        #
        # app.logger.info('%s file_to_upload', profile_img)
        # if profile_img:
        #     upload_result = cloudinary.uploader.upload(profile_img)  # Upload results
        #     app.logger.info(upload_result)

        self.cursor.execute('INSERT INTO user ('
                            'first_name,'
                            'last_name,'
                            'username,'
                            'password,'
                            'email) VALUES(?, ?, ?, ?, ?)', (first_name, last_name,
                                                                username, password, email))
        self.conn.commit()

        return "success"

    def login(self, username):
        self.cursor.execute("SELECT * FROM user WHERE username='{}'".format(username))
        return self.cursor.fetchone()

    def get_user(self, user_id):
        self.cursor.execute("SELECT * FROM user WHERE user_id='{}'".format(user_id))
        return self.cursor.fetchall()

    def update(self, user_id, data):
        if data.get('first_name'):
            self.cursor.execute('UPDATE user SET first_name=? WHERE user_id=?', (data.get('first_name'), user_id))
            self.conn.commit()

        if data.get('last_name'):
            self.cursor.execute('UPDATE user SET last_name=? WHERE user_id=?', (data.get('last_name'), user_id))
            self.conn.commit()

        if data.get('profile_img'):
            # Upload image to cloudinary
            cloudinary.config(cloud_name='ddvdj4vy6', api_key='416417923523248',
                              api_secret='v_bGoSt-EgCYGO2wIkFKRERvqZ0')
            upload_result = None

            app.logger.info('%s file_to_upload', data.get('profile_img'))
            if data.get('profile_img'):
                upload_result = cloudinary.uploader.upload(data.get('profile_img'))  # Upload results
                app.logger.info(upload_result)
                # data = jsonify(upload_result)
            self.cursor.execute('UPDATE user SET profile_img=? WHERE user_id=?', (upload_result['url'], user_id))
            self.conn.commit()

        if data.get('email'):
            self.cursor.execute('UPDATE user SET email=? WHERE user_id=?', (data.get('email'), user_id))
            self.conn.commit()

        if data.get('username'):
            self.cursor.execute('UPDATE user SET username=? WHERE user_id=?', (data.get('username'), user_id))
            self.conn.commit()

        if data.get('password'):
            self.cursor.execute('UPDATE user SET password=? WHERE user_id=?', (data.get('password'), user_id))
            self.conn.commit()

    def delete_user(self, user_id):
        self.cursor.execute("DELETE FROM like WHERE user_id='{}'".format(user_id))
        self.cursor.execute("DELETE FROM dm WHERE sender_id ='{}'".format(user_id))
        self.cursor.execute("DELETE FROM dm WHERE receiver_id ='{}'".format(user_id))
        self.cursor.execute("DELETE FROM comment WHERE user_id ='{}'".format(user_id))
        self.cursor.execute("DELETE FROM post WHERE user_id ='{}'".format(user_id))
        self.cursor.execute("DELETE FROM follow WHERE follower='{}'".format(user_id))
        self.cursor.execute("DELETE FROM follow WHERE followed='{}'".format(user_id))
        self.cursor.execute("DELETE FROM user WHERE user_id='{}'".format(user_id))
        self.conn.commit()

    def post(self, user_id, img, caption, username):
        cloudinary.config(cloud_name='dzzwcmwvn', api_key='354923386558991',
                          api_secret='K4Hwy9i2Glvukp1VlywM5YO2IbE')
        upload_result = None

        app.logger.info('%s file_to_upload', img)
        if img:
            upload_result = cloudinary.uploader.upload(img)  # Upload results
            app.logger.info(upload_result)

        self.cursor.execute('INSERT INTO post (user_id, words, profile_img, username) VALUES(?, ?, ?, ?)',
                            (user_id, caption, upload_result['url'], username))
        self.conn.commit()

    def get_post(self, post_id):
        self.cursor.execute("SELECT * FROM post WHERE post_id='{}'".format(post_id))
        return self.cursor.fetchall()

    def get_follow_posts(self, user_id_list):
        posts = []

        for i in range(len(user_id_list)):
            self.cursor.execute("SELECT * FROM post WHERE user_id={}".format(user_id_list[i]))
            posts.append(self.cursor.fetchone())

        return posts

    def delete_post(self, post_id):
        self.cursor.execute("DELETE FROM post WHERE post_id='{}'".format(post_id))
        self.conn.commit()

    def follow(self, follower, followed):
        self.cursor.execute('INSERT into follow ('
                            'follower,'
                            'followed,'
                            'seen'
                            ') VALUES (? ,?, 0)', (follower, followed))

        self.conn.commit()

    def unfollow(self, follower, followed):
        self.cursor.execute('DELETE FROM follow WHERE followed=? and follower=?', (followed, follower))
        self.conn.commit()

    def get_followers(self, user_id):
        self.cursor.execute("SELECT follower, seen FROM follow WHERE followed='{}'".format(user_id))
        followers = self.cursor.fetchall()

        return followers

    def get_following(self, user_id):
        self.cursor.execute("SELECT followed, seen FROM follow WHERE follower='{}'".format(user_id))
        following = self.cursor.fetchall()

        return following

    def like(self, user_id, post_id):
        self.cursor.execute('INSERT INTO like('
                            'post_id,'
                            'user_id,'
                            ') VALUES (?, ?)', (user_id, post_id))

        self.conn.commit()

    def unlike(self, user_id, post_id):
        self.cursor.execute("DELETE FROM like WHERE post_id=? AND user_id=?", (post_id, user_id))
        self.conn.commit()

    def get_likes(self, post_id):
        self.cursor.execute("SELECT * FROM like WHERE post_id='{}'".format(post_id))
        return self.cursor.fetchall()

    def add_comment(self, post_id, user_id, username, comment):
        self.cursor.execute('INSERT INTO comment (user_id, post_id, username, comment, seen) VALUES (?, ?, ?, ?, 0)',
                            (user_id, post_id,
                             username, comment))
        self.conn.commit()

    def delete_comment(self, comment_id):
        self.cursor.execute("DELETE FROM comment WHERE comment_id='{}'".format(comment_id))
        self.conn.commit()

    def get_comments(self, post_id):
        self.cursor.execute("SELECT * FROM comment WHERE post_id={}".format(post_id))
        return self.cursor.fetchall()

    def search(self, username_string):
        self.cursor.execute("SELECT * FROM user WHERE username LIKE '{}%'".format(username_string))
        return self.cursor.fetchall()


@app.route('/user/', methods=['POST'])
def register():
    response = {}
    db = Database()

    if request.method == 'POST':
        first_name = request.json['first_name']
        last_name = request.json['last_name']
        username = request.json['username']
        password = request.json['password']
        email = request.json['email']

        db.register(first_name, last_name, username, password, email)

        global users
        users = fetch_users()

        response['status_code'] = 200
        response['message'] = "User registered successfully"

    return response


@app.route('/user/<username>')
def login(username):
    response = {}
    db = Database()

    if request.method == 'GET':
        response['status_code'] = 200
        response['message'] = 'User retrieved successfully'
        response['user'] = db.login(username)

    return response


@app.route('/user/<int:user_id>', methods=['GET', 'PATCH', 'PUT'])
def user(user_id):
    response = {}
    db = Database()

    if request.method == 'GET':
        response['status_code'] = 200
        response['message'] = "User retrieved successfully"
        response['user'] = db.get_user(user_id)

    if request.method == 'PATCH':
        incoming_data = dict(request.json)
        db.update(user_id, incoming_data)

        response['status_code'] = 200
        response['message'] = 'User details updated successfully'

    if request.method == 'PUT':
        db.delete_user(user_id)

        response['status_code'] = 200
        response['message'] = 'User deleted successfully'

    global users
    users = fetch_users()

    return response


@app.route('/search/<username_query>/')
def search(username_query):
    response = {}

    db = Database()

    if request.method == "GET":
        response['users'] = db.search(username_query)
        response['status_code'] = 200
        response['message'] = 'Search query successful'

    return response


@app.route('/post/', methods=['GET', 'POST'])
def post():
    response = {}

    db = Database()

    if request.method == 'POST':
        user_id = request.form['user_id']
        profile_img = request.files['profile_img']
        words = request.form['words']
        username = request.form['username']

        db.post(user_id, profile_img, words, username)
        response['status_code'] = 200
        response['message'] = 'Post made successful'

    if request.method == 'GET':
        with sqlite3.connect('cloudiroid.db') as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM post')
            response['posts'] = cursor.fetchall()

        response['status_code'] = 200
        response['message'] = 'Posts retrieved successfully'

    return response


@app.route('/delete_post/<post_id>', methods=['PATCH'])
def delete_post(post_id):
    response = {}
    db = Database()

    if request.method == "PATCH":
        db.delete_post(post_id)
        response['status_code'] = 200
        response['message'] = "Post deleted successfully"

    return response


@app.route('/follow/', methods=['POST', 'PATCH'])
def follow():
    response = {}

    db = Database()

    if request.method == 'GET':
        user_id = request.json['user_id']
        response['followers'] = db.get_followers(user_id)
        response['following'] = db.get_following(user_id)
        response['status_code'] = 200
        response['message'] = 'User follow info retrieved successfully'

    if request.method == "POST":
        follower = request.json['follower']
        followed = request.json['followed']
        db.follow(follower, followed)
        response['status_code'] = 200
        response['message'] = 'Follow interaction successful'

    if request.method == "PATCH":
        follower = request.json['follower']
        followed = request.json['followed']
        db.unfollow(follower, followed)
        response['status_code'] = 200
        response['message'] = 'Unfollow interaction successful'

    return response


@app.route('/follow/<int:user_id>')
def get_followers(user_id):
    response = {}

    db = Database()

    if request.method == 'GET':
        response['followers'] = db.get_followers(user_id)
        response['following'] = db.get_following(user_id)
        response['status_code'] = 200
        response['message'] = 'User follow info retrieved successfully'

    return response


@app.route('/posts/<int:user_id>', methods=['GET'])
def get_posts(user_id):
    response = {}

    db = Database()

    if request.method == 'GET':
        user_follow_data = db.get_following(user_id)
        user_id_list = []

        for i in range(len(user_follow_data)):
            global user_id_lst
            user_id_list.append(int(user_follow_data[i]['followed']))

        print(user_id_list)
        response['status_code'] = 200
        response['message'] = 'posts retrieved successfully'
        response['posts'] = db.get_follow_posts(user_id_list)

    return response


@app.route('/like/<int:post_id>/', methods=['GET', 'POST', 'PATCH'])
@jwt_required()
def like(post_id):
    response = {}
    db = Database()
    user_id = request.json['user_id']

    if request.method == 'GET':
        response['status_code'] = 200
        response['message'] = 'Retrieved like information successfully'
        response['like_data'] = db.get_likes(post_id)

    if request.method == 'POST':
        db.like(user_id, post_id)

        response['status_code'] = 200
        response['message'] = 'Like successful'

    if request.method == 'PATCH':
        db.unlike(user_id, post_id)

        response['status_code'] = 200
        response['message'] = 'Unlike successful'

    return response


@app.route('/comment/', methods=['POST'])
# @jwt_required()
def comment():
    response = {}
    db = Database()

    if request.method == 'POST':
        post_id = request.json['post_id']
        comment = request.json['comment']
        user_id = request.json['user_id']
        username = request.json['username']

        db.add_comment(post_id, user_id, username, comment)

        response['status_code'] = 200
        response['message'] = 'Comment added successfully'

    return response


@app.route('/comment/<int:comment_id>/', methods=['PATCH'])
def delete_comment(comment_id):
    response = {}
    db = Database()

    if request.method == 'PATCH':
        db.delete_comment(comment_id)

        response['status_code'] = 200
        response['message'] = 'Comment deleted successfully'

    return response


@app.route('/comment/<int:post_id>/', methods=['GET'])
def get_comment(post_id):
    response = {}
    db = Database()

    if request.method == 'GET':
        response['comment'] = db.get_comments(post_id)
        response['status_code'] = 200
        response['message'] = 'Comments retrieved successfully'

    return response


if __name__ == '__main__':
    app.run(debug=True)
