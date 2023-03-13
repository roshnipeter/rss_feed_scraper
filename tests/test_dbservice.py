import json
import sqlite3
import sys
import os
import pytest
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../")
import db_service
from app_main import app

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
        response = client.post('/users', json={'user_id': 105, 'password': 'qwerty123'})
        print(response.get_json())
        assert response.status_code == 200
        assert response.get_json() == {"success": True, "message": "User added successfully."}


    