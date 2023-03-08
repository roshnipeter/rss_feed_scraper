import sqlite3

# try:
#     sqlite_connection = sqlite3.connect("rss_feeds.db")
#     cursor = sqlite_connection.cursor()
#     print("DB connection successful")
# except sqlite3.Error as error:
#     print("Error while connecting to sqlite", error)


# def get_data_from_db(query):
#     select_query = query
#     cursor.execute(select_query)
#     data = cursor.fetchall()
#     cursor.close()
#     return data

# def insert_data_to_db_feed(id, url, feed_data):
#     insert_query = "INSERT INTO feeds(id, url, feeddata) VALUES (?,?,?); "
#     cursor.execute(insert_query,(id, url, feed_data))
#     sqlite_connection.commit()
#     cursor.close()

# def insert_data_to_db_feeddata(id, feed_id, title, feed_item, marked,updated):
#     insert_query = "INSERT INTO feed_items(id, feedId, title, feedItem, marked, updated) VALUES (?,?,?,?,?,?); "
#     cursor.execute(insert_query, (id, feed_id, title, feed_item, marked, updated))
#     sqlite_connection.commit()
#     cursor.close()

# def insert_data_to_db_user(cur, user_id, password):
#     insert_query = "INSERT INTO user(user_id, password) VALUES (?,?);"
#     cur.execute(insert_query, (user_id, password))
#     sqlite_connection.commit()
#     cur.close()





