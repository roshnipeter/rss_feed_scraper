from functools import wraps
from flask import Flask, request, jsonify, g
# from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity
import sqlite3
import builder
import json
import os.path
import traceback
import jwt
import auth_service, db_services
from datetime import datetime, timedelta
import config
from  werkzeug.security import generate_password_hash, check_password_hash

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = 'super-secret'  # Change this in production
# jwt = JWTManager(app)


def authenticate(object):
    '''
    Method to check the validity of token passed along with API requests.
    '''
    @wraps(object)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        token = str.replace(str(token), 'Bearer ','')
        if not token:
            response = {"success": False, "message":"Token missing"}
            return response
        try:
            jwt.decode(token, config.config['secret_key'], algorithms=config.config['algorithms'])
        except:
            return {"success": False, "message":"Invalid token"}
        return  object(*args, **kwargs)
    return decorated



@app.before_request
def before_request():
    g.db_connection = sqlite3.connect("rss_feeds.db", timeout=10) #to avoid locking
    g.cursor = g.db_connection.cursor()


@app.teardown_request
def teardown_request(exception):
    if hasattr(g, 'db_connection'):
        g.db_connection.close()

@app.route('/user',methods = ['POST'])
def create_user():
    '''
    Creating a user.
    '''
    
    data = request.get_json()
    userId = data.get('username')
    password = data.get('password')
    if not userId or not password:
        response = {"success": False, "message":"UserID / Password missing."}, 400
        return response
    response = create_user(int(userId), password)
    return response

@app.route('/login',methods = ['POST'])
def login():
    data = request.get_json()
    userId = int(data.get('username'))
    password = data.get('password')
    response = token_validator(userId, password)
    return response


@app.route('/feeds', methods=['GET'])
@authenticate
def list_feeds():
    feeds = g.cursor.execute("""SELECT feeds.url, feedData.feed_data
                                FROM feeds
                                INNER JOIN feedData ON feeds.feed_id = feedData.feed_id
                                WHERE feeds.user_id = 102;""")#get_jwt_identity())
    return jsonify([{
        'url': feed[0],
        'data': json.loads(feed[1]),
    } for feed in feeds])


@app.route('/feeds', methods=['POST'])
@authenticate
def add_feed():
    url = request.json.get('feedUrl')
    if not url:
        return jsonify({'error': 'url is required'}), 400

    userId = 103 #get_jwt_identity()
    hash_key, feed = builder.rss_feeder(url)
    try:
        feed_table_entry = insert_to_feeds(g.cursor, userId, url, hash_key)
        if not feed_table_entry:
            return jsonify({'error': 'Error in database updation'}), 500

        feed_items_table_entry = insert_to_feedItems(g.cursor, hash_key, feed)
        g.cursor.close()
        if not feed_items_table_entry:
            return jsonify({'error': 'Error in database updation'}), 500
        return jsonify({
            'error' : None,
            'success': True,
            'message' : 'Inserted successfully'
        }), 200
    except:
        return jsonify({'error': 'Internal error'}), 500


def insert_to_feeds(userId, url, hash_key):
    try:
        g.cursor.execute("INSERT INTO feeds(user_id, url, feed_id) VALUES (?,?,?); ",(userId,url,hash_key))
        g.db_connection.commit()
        if g.cursor.rowcount == 0:
            return False
        return True
    except sqlite3.IntegrityError:
        traceback.print_exc()
    except:
        traceback.print_exc()


def insert_to_feedItems(hash_key, feeds):
    try:
        g.cursor.execute("INSERT INTO feedData (feed_id, feed_data, marked, updated) VALUES (?,?,?,?);",(hash_key, json.dumps(feeds), 0,0))
        g.db_connection.commit()
        if g.cursor.rowcount == 0:
            return False
        return True
    except sqlite3.IntegrityError:
        #Case when the feed is already handled by some other user. this would be a duplication
        return True
    except:
        traceback.print_exc()


def create_user(userId, password):
    if not userId or not password:
        response = {"success": False, "message":"UserID / Password missing."}, 400
        return response
    response = insert_data_to_user(userId, generate_password_hash(password))
    return response


def insert_data_to_user(user_id, password):
    insert_query = "INSERT INTO user(user_id, password) VALUES (?,?);"
    try:
        g.cursor.execute(insert_query, (user_id, password))
        g.db_connection.commit()
        g.cursor.close()
        return {"success":True, "message":"User created!"}, 200
    except sqlite3.OperationalError:
        return {"success":False, "message":"Database connection error!"}, 500
    except:
        traceback.print_exc()
        return {"success":False, "message":"User not created!"}, 500

def token_validator(user_id, password):
    select_query = "SELECT * FROM user WHERE user_id = ?;"
    try:
        user_data = g.cursor.execute(select_query, (user_id,))# added comma because The reason this happens is that (temp) is an integer but (temp,) is a tuple of length one containing temp.
        if not user_data:
            return {"success":False, "message":"User does not exist!"}, 500
        user_data = user_data.fetchone()
        print(user_data)
        if check_password_hash(user_data[1], password):
                token = jwt.encode({
                                    'user_id': user_data[0],
                                    'exp' : datetime.utcnow() + timedelta(minutes = 60)
                                    }, config.config['secret_key'])
                return {"success":True, "message":"Login successful!", "token":token}
        else:
            return {"success":False, "message":"Invalid password for the user ID."}
    except:
        traceback.print_exc()
        return {"success":False, "message":"Invalid password for the user ID."}, 500


if __name__ == '__main__':
    app.run(port=8000,debug=True)
