import MySQLdb

class zKillboard(object):
    def __init__(self, app):
        self.dbhost = app.config['ZKB']['host']
        self.dbname = app.config['ZKB']['name']
        self.dbuser = app.config['ZKB']['user']
        self.dbpass = app.config['ZKB']['pass']

    def addKey(self, keyid, vcode):
        db = MySQLdb.connect(host=self.dbhost, user=self.dbuser, passwd=self.dbpass, db=self.dbname)
        cur = db.cursor()

        sql = "SELECT keyID FROM zz_api WHERE keyID = %s AND vCode = %s"
        cur.execute(sql, (keyid, vcode))

        existing = cur.fetchall()

        if len(existing) > 0:
            return True

        sql = "INSERT INTO zz_api(keyID, vCode) VALUES (%s, %s)"
        cur.execute(sql, (keyid, vcode))

        db.commit()

        return True
