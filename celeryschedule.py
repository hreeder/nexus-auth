from datetime import timedelta
from celery.schedules import crontab

CELERY_IMPORTS = ("nexus_auth.tasks.dispatcher",)

CELERYBEAT_SCHEDULE = {
    'update-keys': {
        'task': 'nexus_auth.tasks.dispatcher.updateAllKeys',
        'schedule': timedelta(minutes=1)
    },
    'update-all-corps': {
        'task': 'nexus_auth.tasks.dispatcher.updateAllCorps',
        'schedule': timedelta(hours=12)
    },
    'update-all-alliances': {
        'task': 'nexus_auth.tasks.dispatcher.updateAllAlliances',
        'schedule': timedelta(hours=12)
    },
    'update-forum-corp-alliances': {
        'task': 'nexus_auth.tasks.dispatcher.updateForumCorpAllianceAffiliations',
        'schedule': timedelta(hours=6)
    },
    'update-killboard-api-keys': {
        'task': 'nexus_auth.tasks.dispatcher.updateKillboardApiKeys',
        'schedule': crontab(hour=1, minute=0)
    },
    'check-all-users-access': {
        'task': 'nexus_auth.tasks.dispatcher.updateAllUsersAccess',
        'schedule': timedelta(minutes=15)
    }
}
