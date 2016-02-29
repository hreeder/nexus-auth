import json
import requests


class Prosody(object):
    def __init__(self, app, server):
        self.admin_user = app.config['PROSODY']['user']
        self.admin_pass = app.config['PROSODY']['pass']
        self.endpoint = app.config['PROSODY']['endpoint']
        self.server = server
        self.announce_server = app.config['PROSODY'][server]['announce']
        self.name = app.config['PROSODY'][server]['name']

        self.headers = {
            'Host': self.server,
            'Content-Type': 'text/plain'
        }

    def add_user(self, username, password):
        """
        Creates a new user on the service
        :param username: Jabber Username to Create
        :param password: Password for new account
        :return: dict with new user's details, False if unable to create
        """
        payload = json.dumps({
            'server': self.server,
            'username': username,
            'password': password
        })
        request = requests.request(
            'POST',
            self.endpoint + 'user',
            auth=(self.admin_user, self.admin_pass),
            data=payload,
            headers=self.headers
        )

        if request.status_code == 201:
            # We've succeeded, return the new user
            return {
                'username': username + '@' + self.server,
                'password': password
            }

    def check_user(self, username):
        payload = json.dumps({'server': self.server, 'username': username})
        request = requests.request(
            'GET',
            self.endpoint + 'user',
            auth=(self.admin_user, self.admin_pass),
            data=payload,
            headers=self.headers
        )
        if request.status_code == 200:
            return True
        elif request.status_code == 404 and "User does not exist" in request.text:
            return False
        else:
            print request.status_code, request.text
            return True

    def delete_user(self, uid):
        """
        Deletes a user from the service
        :param uid: JID to delete
        :return:
        """
        username, server = uid.lower().split("@")
        payload = json.dumps({
            'server': self.server,
            'username': username
        })
        request = requests.request(
            'DELETE',
            self.endpoint + 'user',
            auth=(self.admin_user, self.admin_pass),
            data=payload,
            headers=self.headers
        )
        if request.status_code == 404 and "User does not exist" in request.text:
            return False
        else:
            return True

    def reset_password(self, uid, password):
        """
        Reset a user's password on the service
        :param uid: User's JID
        :param password: User's new password
        :return:
        """
        username, server = uid.lower().split("@")
        payload = json.dumps({
            'server': self.server,
            'username': username,
            'password': password
        })
        request = requests.request(
            'PATCH',
            self.endpoint + 'user/password',
            auth=(self.admin_user, self.admin_pass),
            data=payload,
            headers=self.headers
        )
        if request.status_code == 200:
            return True
        elif request.status_code == 404:
            return self.add_user(username, password)
        else:
            return False

    def send_multicast(self, target, body):
        body = body.replace('[LT]', '<')
        body = body.replace('[GT]', '>')
        body = body.replace('<br />', '\r')
        payload = ''
        if len(target) >= 1:
            payload = json.dumps({
                'recipients': target,
                'message': body,
                'from': self.admin_user
            })
        else:
            return False

        request = requests.request(
            'POST',
            self.endpoint + 'message',
            auth=(self.admin_user, self.admin_pass),
            data=payload,
            headers=self.headers
        )

        return request.text

    def send_broadcast(self, host, body):
        body = body.replace('[LT]', '<')
        body = body.replace('[GT]', '>')
        body = body.replace('<br />', '\r')

        payload = json.dumps({
            'server': host,
            'message': body
        })

        request = requests.request(
            'POST',
            self.endpoint + 'broadcast',
            auth=(self.admin_user, self.admin_pass),
            data=payload,
            headers=self.headers
        )

        return request.text

    def get_all_online_users(self):
        request = requests.request(
            'GET',
            self.endpoint + 'users',
            auth=(self.admin_user, self.admin_pass),
            headers=self.headers
        )

        return json.loads(request.text)['result']

    def get_online_users_count(self):
        request = requests.request(
            'GET',
            self.endpoint + 'users/count',
            auth=(self.admin_user, self.admin_pass),
            headers=self.headers
        )

        return json.loads(request.text)['result']['count']
