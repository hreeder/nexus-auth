from nexus_auth import app, celery, users
from nexus_auth.models.eve import ApiKey, Corporation, Alliance, STATUS_PENDING, STATUS_OK, TYPE_CORP
from nexus_auth.models.forum import PhpBB
from nexus_auth.models.killboard import zKillboard
from nexus_auth.tasks.eve import updateKeyInfo, updateCorpInfo, updateAllianceInfo
from nexus_auth.tasks.services import checkUsersAccess

from sqlalchemy import asc
from celery.utils.log import get_task_logger

from datetime import datetime, timedelta

logger = get_task_logger(__name__)


@celery.task()
def updateAllKeys():
    keys = ApiKey.query.filter_by(status=STATUS_PENDING).all()
    for key in keys:
        logger.debug('Dispatching task: updateKeyInfo(%s)' % (key.id,))
        updateKeyInfo.delay(key.id)

    if len(keys) < 60:
        logger.debug('Not enough pending keys, getting the oldest keys')
        keys = ApiKey.query.filter_by(status=STATUS_OK).filter(ApiKey.lastUpdated <= datetime.now() - timedelta(hours=1)).order_by(asc(ApiKey.lastUpdated)).limit(60-len(keys)).all()

    for key in keys:
        logger.debug('Dispatching task: updateKeyInfo(%s)' % (key.id,))
        updateKeyInfo.delay(key.id)

@celery.task()
def updateAllUsersAccess():
    allusers = users.getAllUsers()
    for user in allusers:
        checkUsersAccess.delay(user.uid)

@celery.task()
def updateAllCorps():
    corps = Corporation.query.all()
    for corp in corps:
        updateCorpInfo.delay(corp.id)


@celery.task()
def updateAllAlliances():
    alliances = Alliance.query.all()
    for alliance in alliances:
        updateAllianceInfo.delay(alliance.id)    

@celery.task()
def updateForumCorpAllianceAffiliations():
    allusers = users.getAllUsers()
    forum = PhpBB(app)
    for user in allusers:
        forum.setUserProfileFields(user)

@celery.task()
def updateKillboardApiKeys():
    keys = ApiKey.query.filter_by(type=TYPE_CORP, status=STATUS_OK).all()
    zkb = zKillboard(app)
    for key in keys:
        zkb.addKey(key.id, key.vcode)
