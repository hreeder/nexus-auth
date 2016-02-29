import evelink
import MySQLdb
from nexus_auth.models.eve import Character

class PhpBB(object):
    def __init__(self, app):
        self.host = app.config['PHPBB_DB']['host']
        self.name = app.config['PHPBB_DB']['name']
        self.user = app.config['PHPBB_DB']['user']
        self.pswd = app.config['PHPBB_DB']['pass']

    def getForumGroups(self):
        db = MySQLdb.connect(host=self.host, user=self.user, passwd=self.pswd, db=self.name)
        cur = db.cursor()

        query = "SELECT group_id, group_name FROM phpbb_groups"
        cur.execute(query)

        groups = {}
        for group in cur.fetchall():
            groups[group[0]] = {
                'id': group[0],
                'name': group[1]
            }

        return groups

    def isUserInGroup(self, userid, groupid):
        db = MySQLdb.connect(host=self.host, user=self.user, passwd=self.pswd, db=self.name)
        cur = db.cursor()

        query = "SELECT group_id, user_id FROM phpbb_user_group WHERE group_id = %s AND user_id = %s"
        cur.execute(query, (groupid, userid))

        results = cur.fetchall()

        if len(results) > 0:
            return True
        else:
            return False

    def addUserToGroup(self, userid, groupid):
        db = MySQLdb.connect(host=self.host, user=self.user, passwd=self.pswd, db=self.name)
        cur = db.cursor()

        if self.isUserInGroup(userid, groupid):
            return True

        query = "INSERT INTO phpbb_user_group (`group_id`, `user_id`, `group_leader`, `user_pending`) VALUES (%s, %s, 0, 0)"
        cur.execute(query, (groupid, userid))
        db.commit()

        query = "UPDATE `phpbb`.`phpbb_users` SET `user_permissions` = '' WHERE `phpbb_users`.`user_id` = %s"
        cur.execute(query, (userid,))
        db.commit()

        if self.isUserInGroup(userid, groupid):
            return True
        else:
            return False

    def removeUserFromGroup(self, userid, groupid):
        db = MySQLdb.connect(host=self.host, user=self.user, passwd=self.pswd, db=self.name)
        cur = db.cursor()

        query = "DELETE FROM phpbb_user_group WHERE group_id = %s AND user_id = %s"
        cur.execute(query, (groupid, userid))
        db.commit()

        query = "UPDATE `phpbb`.`phpbb_users` SET `user_permissions` = '' WHERE `phpbb_users`.`user_id` = %s"
        cur.execute(query, (userid,))
        db.commit()

        return not self.isUserInGroup(userid, groupid)

    def setUserProfileFields(self, user):
        main = Character.query.filter_by(name=user.username).first()
        if main and main.corp:
            corp = main.corp.name
            if main.corp.alliance:
                alliance = main.corp.alliance.name
            else:
                alliance = ""
        else:
            # query character
            api = evelink.api.API()
            eve = evelink.eve.EVE(api=api)
            charid = eve.character_id_from_name(user.username).result
            if charid:
                info = eve.character_info_from_id(char_id=charid).result
                corp = info['corp']['name']
                alliance = info['alliance']['name']
            else:
                corp = ""
                alliance = ""

        db = MySQLdb.connect(host=self.host, user=self.user, passwd=self.pswd, db=self.name)
        cur = db.cursor()

        query = "SELECT user_id, pf_corp, pf_alliance FROM phpbb_profile_fields_data WHERE user_id = %s"
        cur.execute(query, (user.uid,))

        existing = cur.fetchone()
        if existing:
            query = "UPDATE phpbb_profile_fields_data SET pf_corp=%s, pf_alliance=%s WHERE user_id = %s"
            cur.execute(query, (corp, alliance, user.uid))
        else:
            query = "INSERT INTO phpbb_profile_fields_data (`user_id`, `pf_corp`, `pf_alliance`) VALUES (%s, %s, %s)"
            cur.execute(query, (user.uid, corp, alliance))
        db.commit()
