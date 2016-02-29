from nexus_auth import db, users

TYPE_REGISTERED = 0
TYPE_TEMPORARY = 1

class MumbleAccount(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64))
    display = db.Column(db.String(64))
    password = db.Column(db.String(128))
    account_type = db.Column(db.SmallInteger)
    op_id = db.Column(db.Integer)

class MumbleOperation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url_segment = db.Column(db.String(128))
    owner = db.Column(db.Integer)
    name = db.Column(db.String(64))
    started = db.Column(db.DateTime)
    expires = db.Column(db.DateTime)

    def get_owner(self):
        return users.getUser(userid=self.owner)

    def get_registered_users(self):
        users = MumbleAccount.query.filter_by(account_type=TYPE_TEMPORARY, op_id=self.id).all()
        return users
