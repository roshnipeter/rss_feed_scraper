import sqlite3
import traceback
import json
import jwt
import logging
from flask import jsonify
from dramatiq import actor
from datetime import datetime, timedelta
from  werkzeug.security import generate_password_hash, check_password_hash
import config
import builder


logger = logging.getLogger(__name__)
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
MAX_RETRIES = 5


def get_db_cursor():
    """
    This function returns a tuple of a database connection and a cursor. The database connection is established with the
    sqlite3.connect() method to the local database file "rss_feeds.db" with a timeout of 10 seconds to avoid locking.
    The cursor is created from the database connection to execute SQL statements. The caller function is expected to handle
    closing the cursor and committing or rolling back the changes made with the connection.
    Returns:

    """
    db_connection = sqlite3.connect("rss_feeds.db", timeout=10)
    cursor = db_connection.cursor()
    return db_connection, cursor


@actor()
def update_all_feeds(user_id: int, url: str):
    """
    Updates all the RSS feeds associated with a given user by calling the force_feed_update function for each feed
    Args:
     - user_id: ID of the user
     - url: URL given by the user

    Returns:
     - None
    """
    logger.info("Started")
    force_feed_update.send(user_id, url)
    logger.info("Ended")


def create_user(user_id: int, password: str) -> tuple:
    """
    Method to add user details to the rss_user database.
    Args:
     - user_id : User ID of the logged user
     - password: Password string of the user
    Returns:
        response dict
    """
    if not user_id or not password:
        response = {"success": False, "message": "UserID / Password missing."}, 400
        return response
    response = insert_data_to_user(user_id, generate_password_hash(password))
    return response


def insert_data_to_user(user_id: int, password: str) -> tuple:
    """
    Inserts a new user into the 'user' table of the database.
    Args:
     - user_id: A string representing the username of the new user.
     - password: A string representing the password of the new user.
    Returns:
     - A tuple containing a dictionary with a success message and an HTTP status code.

    The 'insert_data_to_user' method creates an SQL query to insert a new user into the 'user' table of the database.
    It then executes the query using the 'get_db_cursor' helper method to establish a connection to the database and
    create a cursor object. If the insertion is successful, the changes are committed and the connection and cursor
    are closed. If there is a database connection error or any other exception is raised, the changes are rolled back,
    and an error message is returned.

    Example usage:

    Assuming the following parameters:
    user_id = "ABC"
    password = "password"

    The 'insert_data_to_user' method would generate and execute the following SQL query:
    "INSERT INTO user(user_id, password) VALUES (?,?);" with the parameters ('ABC', 'password').

    If the insertion is successful, the method would return the following tuple:
    ({'success': True, 'message': 'User has been created!'}, 200)
    """

    db_connection, cursor = get_db_cursor()
    try:
        check_data = cursor.execute("SELECT * FROM users WHERE user_id=?;", (user_id))
        if check_data:
            cursor.close()
            return {"success": True, "message": "User exists!"}, 200
        cursor.execute("INSERT INTO user(user_id, password) VALUES (?,?);", (user_id, password))
        db_connection.commit()
        cursor.close()
        return {"success": True, "message": "User has been created!"}, 200
    except sqlite3.OperationalError as e:
        traceback.print_exc()
        return {"success": False, "message": "Database connection error!", "error": str(e)}, 500
    except Exception as e:
        traceback.print_exc()
        db_connection.rollback()
        return {"success": False, "message": "User not created!", "error": str(e)}, 500
    finally:
        cursor.close()


def insert_data_to_feed_items_table(user_id: int, hash_key: str, feed_data: list, db_connection: sqlite3.Connection, cursor: sqlite3.Cursor) -> bool:
    """
    This function inserts RSS feed items into the database for a given user and feed URL.
    Args:
     - user_id: ID of the user for whom to insert data.
     - hash_key: Hashed key of the feed url
     - feed_data: List of dictionaries containing feed item data after parsing.
     - db_connection: SQLite3 database connection object.
     - cursor: Cursor object for executing SQL queries.

    Returns:
     - bool: Returns True if the data is inserted successfully, False otherwise.
    """
    try:
        check_data = cursor.execute("SELECT * FROM rss_feedData WHERE feed_id=?;", (hash_key))
        if check_data:
            return True
        count = 0
        for item in feed_data:
            count += 1
            cursor.execute("INSERT INTO rss_feedData (feed_id, feed_item_id, feed_item, marked) VALUES (?,?,?,?);", (hash_key, count, json.dumps(item), 0))
            cursor.execute("INSERT INTO rss_marked_status (user_id, feed_item_id, is_read, feed_id, updated_date) VALUES (?,?,?,?,?);",(user_id, count, 0, hash_key, datetime.now().strftime(DATE_FORMAT)))
        db_connection.commit()
        if cursor.rowcount == 0:
            return False
        return True
    except sqlite3.OperationalError:
        traceback.print_exc()
        return False
    except Exception:
        traceback.print_exc()
        db_connection.rollback()
        return False
    finally:
        cursor.close()


def insert_data_to_feeds(user_id: int, url: str, hash_key: str, db_connection: sqlite3.Connection, cursor: sqlite3.Cursor) -> tuple:
    """This function inserts feed data into the rss_feeds table for a given user.

    Args:
     - user_id: ID of the user for whom to insert data.
     - url: URL of the feed to which the data belongs.
     - hash_key: Hashed key of the feed URL.
     - db_connection: SQLite3 database connection object.
     - cursor: Cursor object for executing SQL queries.

    Returns:
     - tuple: A tuple containing two boolean values indicating the success status of the operation and whether the data is a duplicate.
    """
    try:
        check_data = cursor.execute("SELECT * FROM rss_feeds WHERE user_id=? AND feed_id=?", (user_id, hash_key))
        if check_data:
            return False, True
        cursor.execute("INSERT INTO rss_feeds(user_id, url, feed_id, updated_date) VALUES (?,?,?,?); ", (user_id, url, hash_key, datetime.now().strftime(DATE_FORMAT)))
        db_connection.commit()
        if cursor.rowcount == 0:
            return False, False
        return True, False
    except sqlite3.OperationalError:
        traceback.print_exc()
        return False, False
    except Exception:
        traceback.print_exc()
        return False, False
    finally:
        cursor.close()


def insert_feeds_to_db(user_id: int, url: str) -> tuple:
    """
    Args:
     - user_id: User id for the user who is following the RSS feed
     - url: URL of the RSS feed

    Returns:
     - A tuple containing the result of the operation and the HTTP status code.

    """
    try:
        db_connection, cursor = get_db_cursor()
        hash_key, feed_data = builder.rss_feeder(url)
        feed_table_entry, duplicate = insert_data_to_feeds(user_id, url, hash_key, db_connection, cursor)

        if not feed_table_entry:
            return {"success": False, 'message': 'Error in updating data'}, 500
        if duplicate:
            return {"success": True, 'message': 'URL already followed by user'}, 200

        feed_items_table_entry = insert_data_to_feed_items_table(user_id, hash_key, feed_data, db_connection, cursor)
        if not feed_items_table_entry:
            return {"success": False, 'message': 'Error in database updation'}, 500

        return {'success': True, 'message': 'Inserted successfully'}, 200
    except sqlite3.OperationalError as e:
        traceback.print_exc()
        return {"success": False, "message": "Database connection error!", "error": str(e)}, 500
    except Exception as e:
        return {"success": False, "message": "Insertion error!", "error": str(e)}, 500


def get_marked_items(user_id: int, url: str, marked: int, cursor: sqlite3.Cursor) -> list:
    """
    Retrieves the IDs of the feed items that match the given criteria of being marked or unmarked for a specific user and URL.

    Args:
        user_id: The ID of the user whose feed items are being fetched.
        url: The URL of the feed whose items are being fetched.
        marked: An integer value indicating whether to fetch marked (1) or unmarked (0) feed items.
        cursor: The cursor object to execute SQL queries.

    Returns:
        List: A list of IDs of the feed items matching the criteria, or None if no items were found.
        """
    feed_id_data = cursor.execute("SELECT feed_id FROM rss_feeds WHERE user_id=? AND url=?",(user_id, url))
    if not feed_id_data:
        return []
    feed_id = feed_id_data.fetchone()[0]
    feed_item_data = cursor.execute("SELECT feed_item_id FROM rss_marked_status WHERE feed_id=? AND is_read=?",(feed_id, marked,))
    if not feed_item_data:
        return []
    return [feed[0] for feed in feed_item_data]


def get_feeds(user_id: int, url: str, marked=None) -> tuple:
    """
    Fetches feed items for a given user and URL.

    Args:
     - user_id: ID of the user whose feed items need to be fetched.
     - url: URL of the RSS feed.
     - marked (optional): Marked status of the feed items - 'read' or 'unread'. Defaults to None.

    Returns:
     - Tuple : By default, all items are returned as response(the case when marked is None). If marked is read/ unread, corresponding rows
        are filtered out from the database.
    """
    db_connection, cursor = get_db_cursor()
    try:
        marked_item_ids = []
        if not marked:
            feeds = cursor.execute("""SELECT rss_feeds.url, rss_feedData.feed_item, rss_feedData.feed_item_id
                                  FROM rss_feeds INNER JOIN rss_feedData
                                  ON rss_feeds.feed_id=rss_feedData.feed_id
                                  WHERE rss_feeds.user_id=? ORDER BY datetime(rss_feeds.updated_date) DESC""", (user_id,))
        else:
            if marked == 'read':
                marked_item_ids = get_marked_items(user_id, url, marked=1, cursor=cursor)
            elif marked == 'unread':
                marked_item_ids = get_marked_items(user_id, url, marked=0, cursor=cursor)
            if not marked_item_ids:
                return jsonify({"success": False, 'message': f'No items in the feed that are {marked}.'}), 200

            placeholders = ','.join('?' * len(marked_item_ids))
            feeds = cursor.execute(f"""SELECT rss_feeds.url, rss_feedData.feed_item, rss_feedData.feed_item_id
                                    FROM rss_feeds INNER JOIN rss_feedData
                                    ON rss_feeds.feed_id=rss_feedData.feed_id
                                    WHERE rss_feeds.user_id=? AND rss_feedData.feed_item_id IN ({placeholders})""",([user_id] + marked_item_ids))
            if not feeds:
                return {"success": False, 'message': 'No items identified.'}, 404
        return [{
            'id': feed[2],
            'url': feed[0],
            'data': json.loads(feed[1]),
        } for feed in feeds], 200

    except sqlite3.OperationalError as e:
        traceback.print_exc()
        return {"success": False, "message": "Database connection error!", "error": str(e)}, 500
    except Exception as e:
        traceback.print_exc()
        return {"success": False, "message": 'Error in fetching records', "error": str(e)}, 500
    finally:
        cursor.close()


def mark_read(user_id: int, url: str, item_ids: list) -> tuple:
    """
    Marks a list of item ids as read for the given user and URL.

    Args:
    - user_id: The ID of the user who marked the items as read.
    - url: The URL of the RSS feed.
    - item_ids: A list of item IDs to be marked as read.

    Returns:
    - A response based on the status of marked IDs
    """
    db_connection, cursor = get_db_cursor()
    try:
        feed_id_data = cursor.execute("SELECT feed_id FROM rss_feeds WHERE user_id=? AND url=?",(user_id, url))
        if not feed_id_data:
            return {"success": False, "message": "No data found for the combination!"}, 404
        feed_id = feed_id_data.fetchone()[0]
        for item_id in item_ids:
            cursor.execute("""UPDATE rss_marked_status 
                              SET is_read=1, updated_date=? 
                              WHERE feed_id=? AND feed_item_id=? AND user_id=?""", (datetime.now().strftime(DATE_FORMAT), feed_id, item_id, user_id))
        db_connection.commit()
        return {'success': True, 'message': 'Item ids marked read.'}, 200

    except sqlite3.OperationalError as e:
        traceback.print_exc()
        return {"success": False, "message": "Database connection error!", "error": str(e)}, 500
    except Exception as e:
        traceback.print_exc()
        db_connection.rollback()
        return {"success": False, 'message': 'Error in updating record', "error": str(e)}, 500
    finally:
        cursor.close()


@actor
def force_feed_update(user_id: int, url: str) -> tuple:
    """
    Forces an RSS feed update for a given user and URL by updating the 'updated_date' column in the rss_feeds table
    to the current date and time.
    Args:
     - user_id: The ID of the user who owns the RSS feed.
     - url: The URL of the RSS feed to be updated.
    Returns:
     - A response based on the status of forced update
    """
    db_connection, cursor = get_db_cursor()
    try:
        cursor.execute("UPDATE rss_feeds SET updated_date = ? where user_id=? AND url=?", (datetime.now().strftime(DATE_FORMAT), user_id, url))
        db_connection.commit()
        return {"success": True, "message": "Update successful!"}, 200
    except sqlite3.OperationalError as e:
        traceback.print_exc()
        return {"success": False, "message": "Database connection error!", "error": str(e)}, 500
    except Exception as e:
        traceback.print_exc()
        db_connection.rollback()
        return {"success": False, "message": "Error in force update", "error": str(e)}, 500
    finally:
        cursor.close()


def token_validator(user_id: int, password: str) -> tuple:
    """
    This method validates the token passed along with the API request, and checks if the user exists in the db, and if the
    provided password matches password in the table users. If the user exists and the password is correct, the function
    generates a JWT token and returns it along with a success message and HTTP status code 200. If the user does not exist
    or the password is incorrect, the function returns an error message and HTTP status code 401 or 404.

    Args:
     - user_id: ID of the user
     - password: Password provided by the user

    Returns:
    - A dictionary with keys "success", "message", and "token" (if successful).
    - If successful, HTTP status code 200.
    - If unsuccessful due to incorrect password, HTTP status code 401.
    - If unsuccessful due to user not existing, HTTP status code 404.
    - If there is an error in the function, HTTP status code 500.

    """
    select_query = "SELECT * FROM user WHERE user_id = ?;"
    db_connection, cursor = get_db_cursor()
    try:
        check_data = cursor.execute(select_query, (user_id,))
        if not check_data:
            return {"success": False, "message": "User does not exist!"}, 404
        user_data = check_data.fetchone()
        if check_password_hash(user_data[1], password):
                token = jwt.encode(
                                    {
                                        'user_id': user_data[0],
                                        'exp' : datetime.utcnow() + timedelta(minutes = 60)
                                    }, config.config['secret_key'])
                return {"success": True, "message": "Login successful!", "token":token}, 200
        else:
            return {"success":False, "message": "Invalid password for the user ID."}, 401
    except sqlite3.OperationalError as e:
        traceback.print_exc()
        return {"success": False, "message": "Database connection error!", "error": str(e)}, 500
    except Exception as e:
        traceback.print_exc()
        return {"success":False, "message": "Error in token validation", "error": str(e)}, 500
    finally:
        cursor.close()
