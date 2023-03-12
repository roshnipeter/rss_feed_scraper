from flask import Flask, request, jsonify, g
import builder
import os.path
from datetime import datetime, timedelta
from  werkzeug.security import generate_password_hash, check_password_hash
from auth_service import authenticate
import db_service

app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = 'super-secret'  # Change this in production

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
    response = db_service.token_validator(userId, password)
    return response


@app.route('/feeds', methods=['GET'])
@authenticate
def list_feeds(user_id):
    marked = request.args.get('marked')
    url = request.args.get('feedUrl')
    response = db_service.get_feeds(user_id, url, marked)
    return response 


@app.route('/feeds', methods=['POST'])
@authenticate
def add_feed(user_id):
    url = request.json.get('feedUrl')
    if not url:
        return jsonify({'error': 'url is required'}), 400
    response = db_service.insert_feeds_to_db(user_id, url)
    return response


@app.route('/markread', methods=['PUT'])
@authenticate
def mark_read(user_id):
    url = request.json.get('feedUrl')
    item_id = request.json.get('itemId').split(',')
    if not url:
        return jsonify({'error': 'url is required'}), 400
    response = db_service.mark_read(user_id, url, item_id)
    return response

@app.route('/update', methods=['PUT'])
@authenticate
def force_update(user_id):
    url = request.json.get('feedUrl')
    if not url:
        return jsonify({'error': 'url is required'}), 400
    response = db_service.force_feed_update(user_id, url)
    return response


def create_user(userId, password):
    if not userId or not password:
        response = {"success": False, "message":"UserID / Password missing."}, 400
        return response
    response = db_service.insert_data_to_user(userId, generate_password_hash(password))
    return response


if __name__ == '__main__':
    app.run(port=8000,debug=True)
