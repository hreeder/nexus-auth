from nexus_auth import app, celery, db, users
from nexus_auth.models.mumble import MumbleAccount
from nexus_auth.models.jabber import Prosody
from nexus_auth.utils.services import JabberTools
from nexus_auth.utils.eventlog import post_jabber

from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)


@celery.task()
def checkUsersAccess(userid):
    user = users.getUser(userid=userid)

    if not user.has_services_access():
        # PURRRRGE
        # Delete Mumble Account
        mumbala = MumbleAccount.query.filter_by(id=user.uid).first()

        if mumbala:
            logger.info('Deleted mumble account for user: %s' % (user.username,))
            post_jabber("Nexus_Celery", "SYSTEM", "Deleted Mumble Account for user: %s" % (user.username,))
            db.session.delete(mumbala)
            db.session.commit()

        # Remove any jabber accounts
        sane = JabberTools.sanitize_username(user.username)

        for host in app.config['PROSODY']:
             if isinstance(app.config['PROSODY'][host], dict) and app.config['PROSODY'][host]['purge']:
                 server = Prosody(app, host)
                 if server.check_user(sane):
                     if server.delete_user(sane + "@" + host):
                         logger.info('Deleted Jabber account for user %s on server %s' % (user.username, host))
                         post_jabber("Nexus_Celery", "SYSTEM", "Deleted Jabber Account for user: %s" % (user.username,))
                     else:
                         logger.warn('COULD NOT DELETE JABBER ACCOUNT FOR %s' % (user.username,))
        # WOLOL
