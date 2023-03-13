from email import header
import jwt

import sys
import os
import pytest
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../")
import db_service
from app_main import app
import config

class Test_dbservice:

    @classmethod
    def setup_class(cls):
        cls.db_connection, cls.cursor = db_service.get_db_cursor()


    @classmethod
    def teardown_class(cls):
        cls.cursor.close()
        cls.db_connection.close()
        

    @pytest.fixture
    def client(self):
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client

    def test_create_user(self, client):
        response = client.post('/user', json={'username': 1121, 'password': 'password'})
        print(response.get_json())
        assert response.status_code == 200
        assert response.get_json() == {"success": True, "message": "User has been created!"}

        response = client.post('/user', json={'password': 'password'})
        assert response.status_code == 400
        assert response.get_json() == {"success": False, "message": "UserID / Password missing."}

        response = client.post('/user', json={'username': 1121})
        assert response.status_code == 400
        assert response.get_json() == {"success": False, "message": "UserID / Password missing."}

        response = client.post('/user', json={'username': 1121, 'password': 'password'})
        print(response.get_json())
        assert response.status_code == 200
        assert response.get_json() == {'message': 'User exists!', 'success': True}
    
    def test_get_feeds(self, client):
        token = jwt.encode({'user_id': 107}, config.config['secret_key'], algorithm='HS256')
        response = client.get('/feeds', json={'username': 107, 'feedUrl': 'http://www.nu.nl/rss/Algemeen', 'marked':None}, headers = {'Authorization': f'Bearer {token}'})
        print(response.get_json())
        assert response.status_code == 200
        assert isinstance(response.get_json(), list)
        assert all(isinstance(entry, dict) for entry in response.get_json())

    def test_add_feeds(self, client):
        token = jwt.encode({'user_id': 107}, config.config['secret_key'], algorithm='HS256')
        response = client.post('/feeds', json={'feedUrl': 'http://www.nu.nl/rss/Algemeen'}, headers = {'Authorization': f'Bearer {token}'})
        print(response.get_json())
        assert response.status_code == 200
        assert response.get_json() == {'success': True, 'message': 'Inserted successfully'}

        token = jwt.encode({'user_id': 107}, config.config['secret_key'], algorithm='HS256')
        response = client.post('/feeds', json={'feedUrl': 'http://www.nu.nl/rss/Algemeen'}, headers = {'Authorization': f'Bearer {token}'})
        print(response.get_json())
        assert response.status_code == 200
        assert response.get_json() == {"success": True, 'message': 'URL already followed by user'}

        token = jwt.encode({'user_id': 107}, config.config['secret_key'], algorithm='HS256')
        response = client.post('/feeds', json={'feedUrl': 'http://www.nu.nl/rss/Algemeen'})
        assert response.get_json() == {'message': 'Invalid token', 'success': False}