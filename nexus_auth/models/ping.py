from nexus_auth import db
from nexus_auth.models.groups import Group

TYPE_SERVER = 0
TYPE_GROUP = 1

class PingServer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    servers = db.Column(db.Text)
    display_name = db.Column(db.String(64))

class PingTarget(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    parent_group_id = db.Column(db.Integer, db.ForeignKey('group.id'))
    type = db.Column(db.SmallInteger)
    target = db.Column(db.Integer)

    def get_target_representation(self):
        if self.type == TYPE_SERVER:
            server = PingServer.query.filter_by(id=self.target).first()
            return "Server: " + server.display_name
        elif self.type == TYPE_GROUP:
            group = Group.query.filter_by(id=self.target).first()
            return "Group: " + group.name

    def get_target_name(self):
        if self.type == TYPE_SERVER:
            server = PingServer.query.filter_by(id=self.target).first()
            return server.display_name
        elif self.type == TYPE_GROUP:
            group = Group.query.filter_by(id=self.target).first()
            return group.name

    def get_group(self):
        return Group.query.filter_by(id=self.parent_group_id).first()
