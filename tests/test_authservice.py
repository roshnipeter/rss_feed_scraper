import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../")
import auth_service
import config
import jwt
from app_main import app


class Test_authservice:
    @classmethod
    def setup_class(cls):
        pass

    @classmethod
    def teardown_class(cls):
        pass

    @staticmethod
    @auth_service.authenticate
    def get_userId(user_id): #not static gives a response object of this class.
        return user_id

    def test_authenticate_with_valid_token(self):
        token = jwt.encode({'user_id': 101}, config.config['secret_key'], algorithm='HS256')
        with app.test_request_context(headers={'Authorization': f'Bearer {token}'}):
            response = self.get_userId()
        assert response == 101

    def test_authenticate_with_invalid_token(self):
        with app.test_request_context(headers={'Authorization': f'Bearer invalid token'}):
            response = self.get_userId()
        assert response == {'success': False, 'message': 'Invalid token'}

    def test_authenticate_with_missing_token(self):
        with app.test_request_context():
            response = self.get_userId()
        assert response == {'success': False, 'message': 'Invalid token'}
