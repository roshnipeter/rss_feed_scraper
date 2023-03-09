import sqlite3
import traceback
import json
import jwt
from flask import jsonify
from datetime import datetime, timedelta
import config
from  werkzeug.security import generate_password_hash, check_password_hash

def get_db_cursor():
    db_connection = sqlite3.connect("rss_feeds.db", timeout=10) #to avoid locking
    cursor = db_connection.cursor()
    return db_connection, cursor

def insert_data_to_user(user_id, password):
    insert_query = "INSERT INTO user(user_id, password) VALUES (?,?);"
    try:
        db_connection, cursor = get_db_cursor()
        cursor.execute(insert_query, (user_id, password))
        db_connection.commit()
        cursor.close()
        return {"success":True, "message":"User created!"}, 200
    except sqlite3.OperationalError:
        return {"success":False, "message":"Database connection error!"}, 500
    except:
        traceback.print_exc()
        return {"success":False, "message":"User not created!"}, 500
    finally:
        cursor.close()

def insert_to_feedItems(hash_key, feeds):
    try:
        db_connection, cursor = get_db_cursor()
        cursor.execute("INSERT INTO feedData (feed_id, feed_data, marked, updated) VALUES (?,?,?,?);",(hash_key, json.dumps(feeds), 0,0))
        db_connection.commit()
        if cursor.rowcount == 0:
            return False
        return True
    except sqlite3.IntegrityError:
        #Case when the feed is already handled by some other user. this would be a duplication
        return True
    except:
        traceback.print_exc()
    finally:
        cursor.close()

def insert_to_feeds(userId, url, hash_key):
    try:
        db_connection, cursor = get_db_cursor()
        cursor.execute("INSERT INTO feeds(user_id, url, feed_id) VALUES (?,?,?); ",(userId,url,hash_key))
        db_connection.commit()
        if cursor.rowcount == 0:
            return False
        return True
    except sqlite3.IntegrityError:
        traceback.print_exc()
    except:
        traceback.print_exc()
    finally:
        cursor.close()

def insert_feeds_to_db(userId, url, hash_key, feed):
    feed_table_entry = insert_to_feeds(userId, url, hash_key)
    if not feed_table_entry:
        return jsonify({'error': 'Error in database updation'}), 500
    feed_items_table_entry = insert_to_feedItems(hash_key, feed)
    if not feed_items_table_entry:
        return jsonify({'error': 'Error in database updation'}), 500
    return jsonify({
        'error' : None,
        'success': True,
        'message' : 'Inserted successfully'
    }), 200

def get_feeds(user_id):
    try:
        db_connection, cursor = get_db_cursor()
        feeds = cursor.execute("""SELECT feeds.url, feedData.feed_data
                                FROM feeds
                                INNER JOIN feedData ON feeds.feed_id = feedData.feed_id
                                WHERE feeds.user_id = ?;""",(user_id,))
        return jsonify([{
            'url': feed[0],
            'data': json.loads(feed[1]),
        } for feed in feeds])
    except:
        traceback.print_exc()
    finally:
        cursor.close()

def token_validator(user_id, password):
    print(user_id)
    select_query = "SELECT * FROM user WHERE user_id = ?;"
    try:
        db_connection, cursor = get_db_cursor()
        user_data = cursor.execute(select_query, (user_id,))# added comma because The reason this happens is that (temp) is an integer but (temp,) is a tuple of length one containing temp.
        if not user_data:
            return {"success":False, "message":"User does not exist!"}, 500
        user_data = user_data.fetchone()
        if check_password_hash(user_data[1], password):
                token = jwt.encode({
                                    'user_id': user_data[0],
                                    'exp' : datetime.utcnow() + timedelta(minutes = 60)
                                    }, config.config['secret_key'])
                return {"success":True, "message":"Login successful!", "token":token}
        else:
            return {"success":False, "message":"Invalid password for the user ID."}, 401
    except:
        traceback.print_exc()
        return {"success":False, "message":"Invalid password for the user ID."}, 500
    finally:
        cursor.close()