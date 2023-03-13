# RSS Feeder

This is a flask application that allows a user to follow, parse and store rss feeds. A user of this app can:

1. Follow and unfollow multiple feeds
2. List all feeds registered by them
3. List items belonging to a single feed
4. Update list items as read.
5. List out items of a feed that are read/ unread.
6. Force a feed update (The update is taken place asynchronously in background)

## Technologies used
1. Python(v3.10.4), Flask(2.2.3) -  For building the APIs
2. SQLite(3.37.0) - Used a lighter version of the SQL database.
3. Rabbitmq(3.11.10) - For handling background tasks and asynchronous updates.
4. dramatiq - For schdeduling and runing tasks asynchronoudly in the background
5. JWT for authentication - Since API requires token based authentication, JWT was the best option. This choice can be updated depending on future requirements.
6. pytest - For writing test cases.


## Description of files

1. app_main.py - Contains sourcecode for all the APIs used in the application.
2. auth_service.py - This file has all the code related to authentication of a user.
3. builder.py - This file contains the sourcecode to extract feeds of a URL and generate a hash to store them.
4. config.py - All the configuration variables are stored in config.yaml, and is exposed by this file.
5. db_service.py - This file handles all the methods related to CRUD operations to the db.
6. queue_listener.py - The job that runs in background checking for messages in the queue and further processing them.

## How to run the program?
command to execute is **python app_main.py** Meanwhile, you may run **python queue_listener.py** in another terminal to run update operations in the background.






