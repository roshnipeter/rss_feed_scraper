import jwt
from functools import wraps
from  werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import db_services
from flask import request
import config
import traceback


def authenticate(object):
    '''
    Token authenticator
    '''
    @wraps(object)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization').encode('ascii','ignore')
        token = str.replace(str(token), 'Bearer ','')
        if not token:
            response = {"success": False, "message":"Token missing"}
            return response
        try:
            data = jwt.decode(token.split(" ")[1], config.config['secret_key'], algorithms=config.config['algorithms'])
        except:
            traceback.print_exc()
            response = {"success": False, "message":"Invalid token"}
            return response
        return  object(*args, **kwargs)
    return decorated



def generate_password(password):
    return generate_password_hash(password)


def create_audit_user(cur, userId, password):
    if not userId or not password:
        response = {"success": False, "message":"UserID / Password missing."}, 400
        return response
    response = db_services.insert_data_to_db_user(cur, userId, generate_password(password))
    return response