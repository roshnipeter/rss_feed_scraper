# import sys
# import json
# import os
# sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../")
# from app_main import app

# class TestApp:

#     @classmethod
#     def setup_class(cls):
#         cls.app = app.test_client()

#     def test_create_user(self):
#         data = {'username': 101, 'password': 'test_password'}
#         response = self.app.post('/user', json=data)
#         print(response)
#         assert response.status_code == 200
#         assert json.loads(response.data) == {"success": True, "message": "User created successfully."}

#     def test_login(self):
#         data = {'username': 101, 'password': 'test_password'}
#         response = self.app.post('/login', json=data)
#         assert response.status_code == 200
#         assert json.loads(response.data)['access_token']

#     # def test_list_feeds(self):
#     #     headers = self.get_auth_headers()
#     #     response = self.app.get('/feeds', headers=headers)
#     #     assert response.status_code == 200
#     #     assert json.loads(response.data)['feeds']

#     # def test_add_feed(self):
#     #     headers = self.get_auth_headers()
#     #     data = {'feedUrl': 'http://test.com/rss'}
#     #     response = self.app.post('/feeds', headers=headers, json=data)
#     #     assert response.status_code == 200
#     #     assert json.loads(response.data) == {"success": True, "message": "Feeds added successfully."}

#     # def test_mark_read(self):
#     #     headers = self.get_auth_headers()
#     #     data = {'feedUrl': 'http://test.com/rss', 'itemId': '1'}
#     #     response = self.app.put('/markread', headers=headers, json=data)
#     #     assert response.status_code == 200
#     #     assert json.loads(response.data) == {"success": True, "message": "Marked as read successfully."}

#     # def test_force_update(self):
#     #     headers = self.get_auth_headers()
#     #     data = {'feedUrl': 'http://test.com/rss'}
#     #     response = self.app.put('/update', headers=headers, json=data)
#     #     assert response.status_code == 200
#     #     assert json.loads(response.data)['success'] == True
#     #     assert json.loads(response.data)['message'] == 'Feed update task has been scheduled.'

#     # def get_auth_headers(self):
#     #     data = {'username': 'test_user', 'password': 'test_password'}
#     #     response = self.app.post('/login', json=data)
#     #     access_token = json.loads(response.data)['access_token']
#     #     return {'Authorization': f'Bearer {access_token}'}