import datetime
import evelink
import MySQLdb

from nexus_auth import app, db, users
from nexus_auth.utils.eveapi import MemcacheCache

TYPE_CHARACTER = 0
TYPE_ACCOUNT = 1
TYPE_CORP = 2

TYPES = {
    TYPE_CHARACTER: 'Character',
    TYPE_ACCOUNT: 'Account',
    TYPE_CORP: 'Corporation'
}

STATUS_OK = 0
STATUS_PENDING = 1
STATUS_ERROR = 2
STATUS_ACC_EXPIRED = 3
STATUS_KEY_EXPIRED = 4
STATUS_KEY_INVALID = 5

STATUS = {
    STATUS_OK: 'OK',
    STATUS_PENDING: 'Pending',
    STATUS_ERROR: 'Error',
    STATUS_ACC_EXPIRED: 'Account Expired',
    STATUS_KEY_EXPIRED: 'Key Expired',
    STATUS_KEY_INVALID: 'Key Invalid'
}


class Alliance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    corps = db.relationship('Corporation', backref='alliance', lazy='dynamic')
    ticker = db.Column(db.String(64))


class Corporation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    allianceId = db.Column(db.Integer, db.ForeignKey('alliance.id'))
    characters = db.relationship('Character', backref='corp', lazy='dynamic')
    ticker = db.Column(db.String(64))
    memberCount = db.Column(db.Integer)

    @property
    def apiCoverage(self):
        known_characters = len(self.characters.all())
        members = self.memberCount

        coverage = float(known_characters)/float(members)
        coverage = coverage * 100

        return "%0.2f" % (coverage,)


class Character(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    owner = db.Column(db.Integer)
    corpId = db.Column(db.Integer, db.ForeignKey('corporation.id'))
    lastKnownShip = db.Column(db.Integer)

    def get_valid_api_key(self):
        keys = KeyCharacters.query.filter_by(character_id=self.id).all()
        keys = [ApiKey.query.filter_by(id=map.key_id).first() for map in keys]

        for key in keys:
            if key.status == STATUS_OK:
                return key

        return False

    def get_owner(self):
        return users.getUser(userid=self.owner)


class ApiKey(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    vcode = db.Column(db.String(64))
    desc = db.Column(db.String(64))
    owner = db.Column(db.Integer)
    type = db.Column(db.SmallInteger)
    status = db.Column(db.SmallInteger)
    accessMask = db.Column(db.Integer)
    expiry = db.Column(db.DateTime)
    lastUpdated = db.Column(db.DateTime)

    def __repr__(self):
        return '<API Key %r>' % (self.id,)

    def get_owner(self):
        return users.getUser(userid=self.owner)

    def get_type(self):
        return TYPES[self.type]

    def get_status(self):
        return STATUS[self.status]

    def get_obscure_vcode(self):
        return self.vcode[:5] + "**********" + self.vcode[-5:]


class KeyCharacters(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key_id = db.Column(db.Integer, db.ForeignKey('api_key.id'))
    character_id = db.Column(db.Integer, db.ForeignKey('character.id'))


class KeyTools(object):
    def __init__(self, config):
        self.config = config

    def validateKey(self, uid, vcode):
        cache = MemcacheCache(self.config)
        api = evelink.api.API(cache=cache, api_key=(uid, vcode))
        account = evelink.account.Account(api)

        # Verify that this is an account key
        key_info = account.key_info().result
        characters = account.characters().result

        if key_info['type'] == "account":
            type = TYPE_ACCOUNT
        elif key_info['type'] == "char":
            type = TYPE_CHARACTER
        elif key_info['type'] == "corp":
            type = TYPE_CORP

        if key_info['expire_ts']:
            expiry = datetime.datetime.fromtimestamp(key_info['expire_ts'])
        else:
            expiry = None

        return {
            'type': type,
            'access_mask': key_info['access_mask'],
            'expiry': expiry if expiry else None,
            'charids': [charid for charid in characters]
        }

class EveItem(object):
    SELECT_STATEMENT = "SELECT typeID, typeName FROM invTypes"
    def __init__(self, id, name):
        self.id = id
        self.name = name

    @staticmethod
    def get(typeid):
        sqldb = MySQLdb.connect(host=app.config['SDE']['host'],
                                user=app.config['SDE']['user'],
                                passwd=app.config['SDE']['pass'],
                                db=app.config['SDE']['name'])
        cur = sqldb.cursor()
        cur.execute(EveItem.SELECT_STATEMENT + " WHERE typeID = %s", (typeid,))
        item = cur.fetchone()
        if not item:
            return False

        return EveItem(*item)

    @staticmethod
    def get_by_market_group(marketGroupID):
        sqldb = MySQLdb.connect(host=app.config['SDE']['host'],
                                user=app.config['SDE']['user'],
                                passwd=app.config['SDE']['pass'],
                                db=app.config['SDE']['name'])
        cur = sqldb.cursor()
        cur.execute(EveItem.SELECT_STATEMENT + " WHERE marketGroupID = %s", (marketGroupID,))
        output = []

        for item in cur.fetchall():
            output.append(EveItem(*item))

        return output

    @staticmethod
    def get_by_group(groupID):
        sqldb = MySQLdb.connect(host=app.config['SDE']['host'],
                                user=app.config['SDE']['user'],
                                passwd=app.config['SDE']['pass'],
                                db=app.config['SDE']['name'])
        cur = sqldb.cursor()
        cur.execute(EveItem.SELECT_STATEMENT + " WHERE groupID = %s", (groupID,))
        output = []

        for item in cur.fetchall():
            output.append(EveItem(*item))

        return output


class Region(object):
    SELECT_STATEMENT = "SELECT regionID, regionName FROM mapRegions"
    def __init__(self, id, name):
        self.id = id
        self.name = name

    def __repr__(self):
        return "<EVE Region: %r>" % (self.name,)

    def get_constellations(self):
        return Constellation.get_by_region(self.id)

    @staticmethod
    def get(regionid):
        sqldb = MySQLdb.connect(host=app.config['SDE']['host'],
                                user=app.config['SDE']['user'],
                                passwd=app.config['SDE']['pass'],
                                db=app.config['SDE']['name'])
        cur = sqldb.cursor()

        sql = Region.SELECT_STATEMENT + " WHERE regionID = %s"
        cur.execute(sql, (regionid,))
        data = cur.fetchone()

        if not data: 
            return False

        return Region(*data)

    @staticmethod
    def get_all():
        sqldb = MySQLdb.connect(host=app.config['SDE']['host'],
                                user=app.config['SDE']['user'],
                                passwd=app.config['SDE']['pass'],
                                db=app.config['SDE']['name'])
        cur = sqldb.cursor()

        cur.execute(Region.SELECT_STATEMENT + " WHERE regionID < 11000000 AND regionID NOT IN (10000004, 10000017, 10000019) ORDER BY regionName")
        output = []

        for region in cur.fetchall():
            output.append(Region(*region))

        return output

class Constellation(object):
    SELECT_STATEMENT = "SELECT constellationID, constellationName, regionID FROM mapConstellations"
    def __init__(self, id, name, region_id):
        self.id = id
        self.name = name
        self.region_id = region_id

    def get_systems(self):
        return System.get_by_constellation(self.id)

    @property
    def region(self):
        return Region.get(self.region_id)

    @staticmethod
    def get(constellationid):
        sqldb = MySQLdb.connect(host=app.config['SDE']['host'],
                                user=app.config['SDE']['user'],
                                passwd=app.config['SDE']['pass'],
                                db=app.config['SDE']['name'])
        cur = sqldb.cursor()

        cur.execute(Constellation.SELECT_STATEMENT + " WHERE constellationID = %s", (constellationid,))
        data = cur.fetchone()

        if not data:
            return False
        return Constellation(*data)

    @staticmethod
    def get_by_region(regionid):
        sqldb = MySQLdb.connect(host=app.config['SDE']['host'],
                                user=app.config['SDE']['user'],
                                passwd=app.config['SDE']['pass'],
                                db=app.config['SDE']['name'])
        cur = sqldb.cursor()

        cur.execute(Constellation.SELECT_STATEMENT + " WHERE regionID = %s ORDER BY constellationName", (regionid,))
        output = []
        
        for constellation in cur.fetchall():
            output.append(Constellation(*constellation))

        return output

class System(object):
    SELECT_STATEMENT = "SELECT solarSystemID, solarSystemName, constellationID, regionID, security FROM mapSolarSystems"
    def __init__(self, id, name, constellation_id, region_id, security):
        self.id = id
        self.name = name
        self.constellation_id = constellation_id
        self.region_id = region_id
        self.security = security

    @property
    def region(self):
        return Region.get(self.region_id)

    @property
    def constellation(self):
        return Constellation.get(self.constellation_id)

    @property
    def celestials(self):
        return Celestial.get_by_system(self.id)

    @staticmethod
    def get(systemid):
        sqldb = MySQLdb.connect(host=app.config['SDE']['host'],
                                user=app.config['SDE']['user'],
                                passwd=app.config['SDE']['pass'],
                                db=app.config['SDE']['name'])
        cur = sqldb.cursor()

        cur.execute(System.SELECT_STATEMENT + " WHERE solarSystemID = %s", (systemid,))
        data = cur.fetchone()

        if not data:
            return False

        return System(*data)

    @staticmethod
    def get_by_constellation(constellationid):
        sqldb = MySQLdb.connect(host=app.config['SDE']['host'],
                                user=app.config['SDE']['user'],
                                passwd=app.config['SDE']['pass'],
                                db=app.config['SDE']['name'])
        cur = sqldb.cursor()
        cur.execute(System.SELECT_STATEMENT + " WHERE constellationID = %s", (constellationid,))

        output = []
        for system in cur.fetchall():
            output.append(System(*system))

        return output


class Celestial(object):
    SELECT_STATEMENT = "SELECT itemID, typeID, groupID, itemName, solarSystemID FROM mapDenormalize"
    def __init__(self, id, typeID, groupID, itemName, solarSystemID):
        self.id = id
        self.typeID = typeID
        self.groupID = groupID
        self.name = itemName
        self.solarSystemID = solarSystemID

        if self.groupID == 8:
            self.moongoo = MoonGoo.query.filter_by(moonid=self.id).first()

    @property
    def system(self):
        return System.get(self.solarSystemID)

    @property
    def pos(self):
        if self.groupID != 8:
            return None
        else:
            return POS.query.filter_by(moonid=self.id).first()

    @property
    def goo_1(self):
        if self.moongoo and self.moongoo.goo_1_typeid == 0:
            return "Empty"
        elif self.moongoo:
            return self.moongoo.goo_1_typeid
        else:
            return None

    @property
    def goo_2(self):
        if self.moongoo and self.moongoo.goo_2_typeid == 0:
            return "Empty"
        elif self.moongoo:
            return self.moongoo.goo_2_typeid
        else:
            return None

    @property
    def goo_3(self):
        if self.moongoo and self.moongoo.goo_3_typeid == 0:
            return "Empty"
        elif self.moongoo:
            return self.moongoo.goo_3_typeid
        else:
            return None

    @property
    def goo_4(self):
        if self.moongoo and self.moongoo.goo_4_typeid == 0:
            return "Empty"
        elif self.moongoo:
            return self.moongoo.goo_4_typeid
        else:
            return None

    @staticmethod
    def get(celestialid):
        sqldb = MySQLdb.connect(host=app.config['SDE']['host'],
                                user=app.config['SDE']['user'],
                                passwd=app.config['SDE']['pass'],
                                db=app.config['SDE']['name'])
        cur = sqldb.cursor()
        cur.execute(Celestial.SELECT_STATEMENT + " WHERE itemID = %s", (celestialid,))

        data = cur.fetchone()
        if not data:
            return False

        return Celestial(*data)

    @staticmethod
    def get_by_system(solarsystemid):
        sqldb = MySQLdb.connect(host=app.config['SDE']['host'],
                                user=app.config['SDE']['user'],
                                passwd=app.config['SDE']['pass'],
                                db=app.config['SDE']['name'])
        cur = sqldb.cursor()
        cur.execute(Celestial.SELECT_STATEMENT + " WHERE solarSystemID = %s AND groupID IN (7,8,9,15) ORDER BY itemID", (solarsystemid,))

        output = []
        for row in cur.fetchall():
            output.append(Celestial(*row))

        return output

class POS(db.Model):
    moonid = db.Column(db.Integer, primary_key=True)
    tower_typeid = db.Column(db.Integer)
    date_added = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    author = db.Column(db.Integer)
    corpid = db.Column(db.Integer)
    corp_ticker = db.Column(db.String(32))

    @property
    def corp(self):
        return Corporation.query.filter_by(id=self.corpid).first()

class MoonGoo(db.Model):
    moonid = db.Column(db.Integer, primary_key=True)
    goo_1_typeid = db.Column(db.Integer)
    goo_2_typeid = db.Column(db.Integer)
    goo_3_typeid = db.Column(db.Integer)
    goo_4_typeid = db.Column(db.Integer)
    last_updated = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    last_editor = db.Column(db.Integer)

    def goo_string(self):
        output = ""

        if self.goo_1_typeid == 0:
            output += "Empty, "
        elif self.goo_1_typeid:
            output += EveItem.get(self.goo_1_typeid).name + ", "
        else:
            output += "Unscanned, "

        if self.goo_2_typeid == 0:
            output += "Empty, "
        elif self.goo_2_typeid:
            output += EveItem.get(self.goo_2_typeid).name + ", "
        else:
            output += "Unscanned, "

        if self.goo_3_typeid == 0:
            output += "Empty, "
        elif self.goo_3_typeid:
            output += EveItem.get(self.goo_3_typeid).name + ", "
        else:
            output += "Unscanned, "

        if self.goo_4_typeid == 0:
            output += "Empty"
        elif self.goo_4_typeid:
            output += EveItem.get(self.goo_4_typeid).name
        else:
            output += "Unscanned"

        return output
