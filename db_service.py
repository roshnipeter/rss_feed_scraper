import sqlite3
import trace
import traceback
import json
import jwt
from flask import jsonify
from datetime import datetime, timedelta
import config
import builder
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

def insert_to_feedItems(user_id, hash_key, feed_data, db_connection, cursor):
    try:
        check_data = cursor.execute("SELECT * FROM rss_feedData WHERE feed_id=?;",(hash_key))
        if check_data:
            # No need to update since feed already added.
            return True
        count = 0
        for item in feed_data:
            count += 1
            cursor.execute("INSERT INTO rss_feedData (feed_id, feed_item_id, feed_item, marked) VALUES (?,?,?,?);",(hash_key, count, json.dumps(item), 0))
            cursor.execute("INSERT INTO rss_marked_status (user_id, feed_item_id, is_read, feed_id, updated_date) VALUES (?,?,?,?,?);",(user_id, count,0,hash_key,datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
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

def insert_to_feeds(userId, url, hash_key, db_connection, cursor):
    '''
    Returns status, duplicate
    '''
    try:
        check_data = cursor.execute("SELECT * FROM rss_feeds WHERE user_id=? AND feed_id=?",(userId, hash_key))
        if check_data:
            return False, True
        cursor.execute("INSERT INTO rss_feeds(user_id, url, feed_id, updated_date) VALUES (?,?,?,?); ",(userId,url,hash_key, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        db_connection.commit()
        if cursor.rowcount == 0:
            return False, False
        return True, False
    except sqlite3.IntegrityError:
        traceback.print_exc()
    except:
        traceback.print_exc()
    finally:
        cursor.close()

def insert_feeds_to_db(userId, url):
    try:
        db_connection, cursor = get_db_cursor()
        hash_key, feed_data = builder.rss_feeder(url)
        feed_table_entry, duplicate = insert_to_feeds(userId, url, hash_key,db_connection, cursor)
        if not feed_table_entry:
            return jsonify({"success":False, 'message': 'Error in updating data'}), 500
        if duplicate:
            return jsonify({"success":True, 'message': 'URL already followed by user'}), 200
        feed_items_table_entry = insert_to_feedItems(userId, hash_key, feed_data, db_connection, cursor)
        if not feed_items_table_entry:
            return jsonify({'error': 'Error in database updation'}), 500
        return jsonify({
            'error' : None,
            'success': True,
            'message' : 'Inserted successfully'
        }), 200
    except:
        return jsonify({'error': 'Error in inserting records'}), 500

def get_marked_items(user_id, url, marked, cursor):
    feed_id_data = cursor.execute("SELECT feed_id FROM rss_feeds WHERE user_id=? AND url=?",(user_id,url))
    if not feed_id_data:
        return None
    # print(feed_id_data.fetchone()[0])
    feed_id = feed_id_data.fetchone()[0]
    feed_item_data = cursor.execute("SELECT feed_item_id FROM rss_marked_status WHERE feed_id=? AND is_read=?",(feed_id,marked,))
    if not feed_item_data:
        return None
    return [feed[0] for feed in feed_item_data]


def get_feeds(user_id, url, marked = None):
    try:
        db_connection, cursor = get_db_cursor()
        if not marked:
            feeds = cursor.execute("""SELECT rss_feeds.url, rss_feedData.feed_item, rss_feedData.feed_item_id
                                  FROM rss_feeds INNER JOIN rss_feedData
                                  ON rss_feeds.feed_id=rss_feedData.feed_id
                                  WHERE rss_feeds.user_id=? ORDER BY datetime(rss_feeds.updated_date) AS""",(user_id,))
        else:
            if marked == 'read':
                marked_item_ids = get_marked_items(user_id,url,marked=1, cursor=cursor)
            elif marked == 'unread':
                marked_item_ids = get_marked_items(user_id,url,marked=0, cursor=cursor)
            if not marked_item_ids:
                return jsonify({"success":False, 'message': f'No items in the feed that are {marked}.'}), 200

            placeholders = ','.join('?' * len(marked_item_ids))
            feeds = cursor.execute(f"""SELECT rss_feeds.url, rss_feedData.feed_item, rss_feedData.feed_item_id
                                    FROM rss_feeds INNER JOIN rss_feedData
                                    ON rss_feeds.feed_id=rss_feedData.feed_id
                                    WHERE rss_feeds.user_id=? AND rss_feedData.feed_item_id IN ({placeholders})""",([user_id] + marked_item_ids))
        return jsonify([{
            'id': feed[2],
            'url': feed[0],
            'data': json.loads(feed[1]),
        } for feed in feeds])
    except:
        traceback.print_exc()
        return jsonify({'error': 'Error in fetching records'}), 500
    finally:
        cursor.close()

def mark_read(user_id, url, item_ids): #Future - Have the option to mark unread also.

    db_connection, cursor = get_db_cursor()
    try:
        feed_id_data = cursor.execute("SELECT feed_id FROM rss_feeds WHERE user_id=? AND url=?",(user_id,url))
        if not feed_id_data:
            return None
        # print(feed_id_data.fetchone()[0])
        feed_id = feed_id_data.fetchone()[0]
        for item_id in item_ids:
            feed_item_data = cursor.execute("""UPDATE rss_marked_status 
                                            SET is_read=1, updated_date=? 
                                            WHERE feed_id=? AND feed_item_id=? AND user_id=?""",
                                            (datetime.now().strftime("%Y-%m-%d %H:%M:%S"),feed_id,item_id,user_id))
        db_connection.commit()
        return jsonify({
            'error' : "",
            'success': True,
            'message' : 'Item ids marked read.'
        }), 200
    except:
        traceback.print_exc()
        return jsonify({"success":False, 'message': 'Error in updating record'}), 500
    finally:
        cursor.close()

def force_feed_update(user_id, url):
    try:
       db_connection, cursor = get_db_cursor()
       cursor.execute("UPDATE rss_feeds SET updated_date = ? where user_id=? AND url=?", (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), user_id, url)) 
       db_connection.commit()
       return {"success":True, "message":"Update successful!"}, 200
    except:
        traceback.print_exc()
        return {"success":False, "message":"Error in force update"}, 500
    finally:
        cursor.close()

def token_validator(user_id, password):
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