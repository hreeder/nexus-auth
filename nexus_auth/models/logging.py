from nexus_auth import db

import datetime

class AuditLogEntry(db.Model):
    __tablename__ = "log_general"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    area = db.Column(db.String(64))
    action_type = db.Column(db.String(64))
    action_item = db.Column(db.Text)
    time = db.Column(db.DateTime, default=datetime.datetime.utcnow())
