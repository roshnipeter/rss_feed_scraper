import jwt
import config
import traceback
from flask import request
from functools import wraps


def authenticate(auth_object):
    """
    A decorator that authenticates the user by verifying a JWT token in the Authorization header of the request.
    Args:
        auth_object: A function that requires authentication, and expects a user_id as its first argument.
    Returns:
        A decorated version of auth_object that performs authentication before calling it.
    The decorator checks for the presence of an Authorization header in the request, extracts the JWT token from it, and decodes the token using a secret key and a set of allowed algorithms specified in the application's configuration file. If the token is missing or invalid, the decorator returns a response with an error message. Otherwise, it calls auth_object with the user_id extracted from the token and the arguments passed to the decorated function.

    Example usage:

    @authenticate
    def my_secure_function(user_id, arg1, arg2, ...):
        # do something secure with user_id and the arguments
    """
    @wraps(auth_object)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        token = str.replace(str(token), 'Bearer ', '')
        if not token:
            response = {"success": False, "message": "Token missing"}
            return response
        try:
            data = jwt.decode(token, config.config['secret_key'], algorithms=config.config['algorithms'])
        except Exception as e:
            traceback.print_exc(e)
            return {"success": False, "message": "Invalid token"}
        return auth_object(data['user_id'], *args, **kwargs)
    return decorated