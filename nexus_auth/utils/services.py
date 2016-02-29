import json
from time import gmtime, strftime

from nexus_auth import users
from nexus_auth.models.groups import Group, GroupMember, APPLICATION_ACCEPTED
from nexus_auth.models.jabber import Prosody
from nexus_auth.models.ping import PingServer, PingTarget
from nexus_auth.utils.eventlog import log_event

from flask.ext.login import current_user

class JabberTools(object):
    def __init__(self, app):
        self.app = app
        self.hosts = {}
        for key in app.config['PROSODY']:
            if isinstance(app.config['PROSODY'][key], dict):
                self.hosts[key] = app.config['PROSODY'][key]
        self.cfg = app.config['PROSODY']

    def getHosts(self):
        return self.hosts

    def getAllServers(self):
        return [Prosody(self.app, server) for server in self.hosts]

    def getVisibleServers(self, user):
        user_groups = user.get_group_ids()
        output = []
        for server in self.hosts:
            if self.hosts[server]['required'] in user_groups:
                output.append(Prosody(self.app, server))

        return output

    def broadcast(self, targets, body, sender, important=False, fleet=False):
        target_names = []
        group_ids = []
        servers = []
        
        for target in targets:
            type, destination = target.split('-')
            if type == "svr":
                server = PingServer.query.filter_by(id=destination).first()
                target_names.append(server.display_name)
                lst_servers = json.loads(server.servers)
                servers.extend(lst_servers)
            elif type=="grp":
                group_ids.append(destination)
                group = Group.query.filter_by(id=destination).first()
                target_names.append(group.name)

        body = "\r\n" + body
        if fleet:
            body += "\r\n\r\n" + fleet + "\r\n"
        else:
            body += "\r\n\r\n"
        body += "== Sent to %s by %s at %s EVE ==" % (', '.join(target_names), sender.username, strftime("%Y/%m/%d %H:%M", gmtime()))
        if important:
            body += "\r\n:frogsiren: :frogsiren: :frogsiren: :frogsiren: :frogsiren: :frogsiren: :frogsiren: :frogsiren:"

        for server in set(servers):
            jserver = Prosody(self.app, server)
            jserver.send_broadcast(server, body)

        userids = []
        jids = []
        for group in group_ids:
            members = GroupMember.query.filter_by(group_id=group, app_status=APPLICATION_ACCEPTED).all()
            userids.extend([member.member_id for member in members])

        for id in set(userids):
            user = users.getUser(userid=id)
            jids.extend(user.get_jabber_ids())

        jabberserver = Prosody(self.app, 'negativewaves.co.uk')
        jabberserver.send_multicast(jids, body)

        log_event('Broadcast', 'send', current_user, body)

    @staticmethod
    def sanitize_username(input):
        """
        Converts a username to a jabber safe username
        :param input: Username to convert
        :return: jid safe name
        """
        out = ""
        for char in input:
            if char == " ":
                out += "_"
            elif char == "'":
                pass
            else:
                out += char.lower()

        return out

