from flask import Flask
from flask.ext.login import LoginManager, current_user
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.principal import Principal, identity_loaded, UserNeed, RoleNeed

app = Flask(__name__)
app.config.from_object('config')
db = SQLAlchemy(app)
login = LoginManager()
login.init_app(app)
login.login_view = 'login'
Principal(app)

from nexus_auth.models.users import UserTools
users = UserTools()

from nexus_auth.models.groups import GroupTools
grouptools = GroupTools()

from nexus_auth.models.eve import KeyTools
keytools = KeyTools(app.config)

from nexus_auth.utils.services import JabberTools
jabbertools = JabberTools(app)

from celeryschedule import CELERYBEAT_SCHEDULE, CELERY_IMPORTS
app.config['CELERYBEAT_SCHEDULE'] = CELERYBEAT_SCHEDULE
app.config['CELERY_IMPORTS'] = CELERY_IMPORTS

from nexus_auth.utils.celerytools import make_celery
celery = make_celery(app)

@login.user_loader
def load_user(username):
    return users.getUser(username=username)

from permissions import ACTIVE_ROLES

@identity_loaded.connect_via(app)
def on_identity_loaded(sender, identity):
    identity.user = current_user
    if current_user.is_anonymous():
        return False

    if hasattr(current_user, 'uid'):
        identity.provides.add(UserNeed(current_user.uid))

    if current_user.is_admin():
        for role in ACTIVE_ROLES:
            identity.provides.add(RoleNeed(role))
    else:
        groupPermissions = current_user.get_roles()
        for permission in groupPermissions:
            if permission in ACTIVE_ROLES:
                identity.provides.add(RoleNeed(permission))

from sqlalchemy import exc
from sqlalchemy import event
from sqlalchemy.pool import Pool

@event.listens_for(Pool, "checkout")
def ping_connection(dbapi_connection, connection_record, connection_proxy):
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute("SELECT 1")
    except:
        # optional - dispose the whole pool
        # instead of invalidating one at a time
        # connection_proxy._pool.dispose()

        # raise DisconnectionError - pool will try
        # connecting again up to three times before raising.
        print "raise error"
        raise exc.DisconnectionError()
    cursor.close()

from nexus_auth.views import core, eve, groups, exceptions, services, ping, permissions, timers, hr, recon, api
from nexus_auth.models import eve, groups, ping, timers, logging
from nexus_auth.utils import filters
