import MySQLdb

from .groups import Group, GroupMember, APPLICATION_ACCEPTED

from nexus_auth import app
from nexus_auth.permissions import ACTIVE_ROLES

from flask.ext.login import UserMixin

from phpbb.auth.sql import setup as phpbb_setup
from phpbb.auth.auth_db import login_db as phpbb_login

from sqlalchemy import asc


class User(UserMixin):
    def __init__(self, uid, username, email):
        self.uid = uid
        self.username = username
        self.email = email

    def get_id(self):
        return self.username

    def is_admin(self):
        for group in self.get_groups():
            if group.group.id == 1:
                return True
        return False

    def get_groups(self):
        return GroupMember.query.filter_by(member_id=self.uid, app_status=APPLICATION_ACCEPTED).order_by(asc(GroupMember.group_id)).all()

    def get_group_ids(self):
        groups = self.get_groups()
        return [g.group.id for g in groups]

    def get_roles(self):
        groups = [group.group for group in self.get_groups()]
        roles = []
        for group in groups:
            roles.extend([permission.permission for permission in group.permissions.all()])
        return list(set(roles))

    def has_role(self, role):
        if role not in ACTIVE_ROLES:
            return False
        if self.is_admin(): return True
        return role in self.get_roles()

    def has_alliance_access(self):
        if app.config['ALLIANCE_SERVICES_GROUP_ID'] in self.get_group_ids():
            return True
        else:
            return False

    def has_services_access(self):
        ids = self.get_group_ids()
        valid_groups = Group.query.filter_by(category_id=3).all()
        if valid_groups:
            for group in valid_groups:
                if group.id in ids:
                    return True
        return False

    def get_jabber_ids(self):
        from nexus_auth import jabbertools
        if not self.has_services_access():
            return []

        sane = jabbertools.sanitize_username(self.username)
        output = []
        for server in jabbertools.getVisibleServers(self):
            output.append(sane + "@" + server.server)

        return output

    def get_main(self):
        from .eve import Character
        return Character.query.filter_by(owner=self.uid, name=self.username).first()

    def can_ping(self):
        from .ping import PingTarget
        targets = PingTarget.query.filter(PingTarget.parent_group_id.in_(self.get_group_ids())).all()
        return bool(targets)

    def get_mumblename(self):
        return self.username.replace("'", "")

    def get_api_keys(self):
        from .eve import ApiKey
        return ApiKey.query.filter_by(owner=self.uid).all()

    def get_all_characters(self):
        from nexus_auth.models.eve import Character
        output = []
        allchars = Character.query.filter_by(owner=self.uid).all()
        for toon in allchars:
            if toon.corpId:
                output.append(toon)
        return output

    def can_view_corp(self, corpid):
        if self.is_admin():
            return True

        if self.has_role('view-any-corp-members'):
            return True

        if not self.has_role('view-own-corp-members'):
            return False

        chars = self.get_all_characters()
        for char in chars:
            if char.corpId == corpid:
                return True
        return False


class UserTools(object):
    def __init__(self):
        pass

    def getUser(self, username=None, userid=None):
        if not userid and not username:
            return False

        query = "SELECT user_id, username, user_email FROM phpbb_users WHERE"

        if userid:
            query += " user_id = %s"
            term = userid
        elif username:
            query += " username_clean = %s"
            term = username.lower().encode("UTF-8").replace("'", u"\u02b9")

        db = MySQLdb.connect(host=app.config['PHPBB_DB']['host'], user=app.config['PHPBB_DB']['user'],
                             passwd=app.config['PHPBB_DB']['pass'], db=app.config['PHPBB_DB']['name'], charset='utf8')
        cur = db.cursor()
        cur.execute(query, (term,))
        data = cur.fetchone()

        if not data:
            return False

        return User(data[0], data[1], data[2])

    def getAllUsers(self):
        db = MySQLdb.connect(host=app.config['PHPBB_DB']['host'], user=app.config['PHPBB_DB']['user'],
                             passwd=app.config['PHPBB_DB']['pass'], db=app.config['PHPBB_DB']['name'])
        cur = db.cursor()
        cur.execute('SELECT user_id, username, user_email FROM phpbb_users')

        output = []

        for user in cur.fetchall():
            output.append(User(user[0], user[1], user[2]))

        return output

    def checkCredentials(self, username, password):
        db = MySQLdb.connect(host=app.config['PHPBB_DB']['host'], user=app.config['PHPBB_DB']['user'],
                             passwd=app.config['PHPBB_DB']['pass'], db=app.config['PHPBB_DB']['name'], charset='utf8')
        phpbb_setup(db)
        result, user_row = phpbb_login(username, password)

        if result == "LOGIN_SUCCESS":
            return True
        else:
            return False
