from flask import Flask, request, jsonify, g
from auth_service import authenticate
import db_service
from dramatiq import actor
from flask_dramatiq import Dramatiq
from dramatiq.results import Results

app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = 'super-secret'  # Change this in production

dramatiq = Dramatiq(app)
dramatiq.broker = 'amqp://guest:guest@rabbitmq:5672'

@actor()
def update_feeds(user_id, url) -> None:
    """
    This method is used to update all feeds for a given user and url. This is scheduled to update asynchronously in the background
        Parameters:
            user_id : ID of the user whose feed needs to be updated
            url: URL that requires updation
        Returns:
            None
    """
    print("Updating feeds...")
    db_service.update_all_feeds(user_id, url)
    print("Updating feeds completed")


@app.route('/user',methods = ['POST'])
def create_user() -> tuple:
    """
    Creates a user in the database. The updated table is rss_user/
        Parameters:
            None
        Returns:
            response dict
    """
    data = request.get_json()
    user_id = data.get('username')
    password = data.get('password')
    if not user_id or not password:
        response = {"success": False, "message":"UserID / Password missing."}, 400
        return response
    response = db_service.create_user(int(user_id), password)
    return response


@app.route('/login',methods = ['POST'])
def login() -> dict:
    """
    This method is used to login a user. 
        Parameters:
            None
        Returns:
            response dict
    """
    data = request.get_json()
    user_id = int(data.get('username'))
    password = data.get('password')
    response = db_service.token_validator(user_id, password)
    return response


@app.route('/feeds', methods=['GET'])
@authenticate
def list_feeds(user_id) -> dict:
    """
    List out all feeds followed by a user. There's option to filter out only read/unread feeds of a followed URL as well.
        Parameters:
            user_id : User ID of the logged user
        Returns:
            response dict
    """
    marked = request.args.get('marked')
    url = request.args.get('feedUrl')
    response = db_service.get_feeds(user_id, url, marked)
    return response 


@app.route('/feeds', methods=['POST'])
@authenticate
def add_feed(user_id):
    """
    Add RSS feeds of a URL. 
        Parameters:
            user_id : User ID of the logged user
        Returns:
            response dict
    """
    url = request.json.get('feedUrl')
    if not url:
        return jsonify({'error': 'url is required'}), 400
    response = db_service.insert_feeds_to_db(user_id, url)
    return response


@app.route('/markread', methods=['PUT'])
@authenticate
def mark_read(user_id) -> tuple:
    """
    Method to mark a feed item as read. 
        Parameters:
            user_id : User ID of the logged user
        Returns:
            response dict
    """
    url = request.json.get('feedUrl')
    item_id = request.json.get('itemId').split(',')
    if not url:
        return {"success":False, "message":"Please provide feedUrl!"}, 400
    response = db_service.mark_read(user_id, url, item_id)
    return response

@app.route('/update', methods=['PUT'])
@authenticate
def force_update(user_id) -> tuple:
    """
    Force update a feed that's followed by the user. 
        Parameters:
            user_id : User ID of the logged user
        Returns:
            response dict
    """
    url = request.json.get('feedUrl')
    if not url:
        return {"success":False, "message":"Please provide feedUrl!"}, 400
    result = update_feeds.send(user_id, url)
    return {'success': True, 'message': 'Feed update task has been scheduled.', 'task_id':result.message_id}, 200

"""
@app.route('/update/status/<string:task_id>', methods=['GET'])
@authenticate
def update_status(user_id, task_id):
    '''
    Force update a feed that's followed by the user. 
        Parameters:
            user_id : User ID of the logged user
        Returns:
            response dict
    '''
    result_data = Results.get_result(task_id)
    if result_data.is_successful():
        return {'success': True, 'message': 'Task completed successfully.'}, 200
    elif result_data.is_failed():
        return {'success': False, 'message': 'Task failed.'}, 200
    else:
        return {'success': False, 'message': 'Task is still running.'}, 200
"""

if __name__ == '__main__':
    app.run(port=8000,debug=True)
