from nexus_auth import app, db
from nexus_auth.models.logging import AuditLogEntry
import requests

def log_event(origin, action, user, message, log_db=True, log_jabber=True):
    if log_db:
        entry = AuditLogEntry(user_id=user.uid,
                              area=origin.lower(),
                              action_type=action.lower(),
                              action_item=message)
        db.session.add(entry)
        db.session.commit()

    if log_jabber:
        post_jabber(origin, user.username, message)


def post_jabber(origin, username, message):
        post_url = app.config['LOGBOT']['url']
        secret_key = app.config['LOGBOT']['key']

        logbot_args = {
            'key': secret_key,
            'tag': "Nexus",
            'tag2': origin,
            'message': username + ": " + message
        }
        request = requests.request('POST', post_url, data=logbot_args)
