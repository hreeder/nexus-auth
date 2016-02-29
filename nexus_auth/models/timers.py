from nexus_auth import db
import calendar
import json
import time

class Timer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    system = db.Column(db.String(12))
    planet = db.Column(db.String(6))
    moon = db.Column(db.Integer)
    owner = db.Column(db.String(64))
    time = db.Column(db.DateTime)
    notes = db.Column(db.String(256))
    author = db.Column(db.Integer)

    def __init__(self, system, planet, moon, owner, time, notes, author):
        self.system = system
        self.planet = planet
        self.moon = moon
        self.owner = owner
        self.time = time
        self.notes = notes
        self.author = author

    def __repr__(self):
        return '<Timer %r>' % self.time

    def to_unix_time(self):
        # return int(time.mktime(self.time.timetuple()))
        return int(calendar.timegm(self.time.timetuple()))

    def to_json(self):
        return json.dumps(self.to_dict())

    def to_dict(self):
        return {
            "id": self.id,
            "system": self.system,
            "planet": self.planet,
            "moon": self.moon,
            "owner": self.owner,
            "time": self.to_unix_time(),
            "notes": self.notes,
            "author": self.author,
        }

    def get_author(self):
        from nexus_auth import users
        return users.getUser(userid=self.author)
