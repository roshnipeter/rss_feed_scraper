from functools import wraps
import traceback
from flask import request
import jwt
import config

def authenticate(object):
    '''
    Method to check the validity of token passed along with API requests
    '''
    @wraps(object)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        token = str.replace(str(token), 'Bearer ','')
        if not token:
            response = {"success": False, "message":"Token missing"}
            return response
        try:
            data = jwt.decode(token, config.config['secret_key'], algorithms=config.config['algorithms'])
            print(data)
        except:
            traceback.print_exc()
            return {"success": False, "message":"Invalid token"}
        return object(data['user_id'], *args, **kwargs)
    return decorated

