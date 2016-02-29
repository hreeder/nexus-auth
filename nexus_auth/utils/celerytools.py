from nexus_auth import app, db
from celery import Celery

from celery.signals import worker_process_init, import_modules

@worker_process_init.connect
def celery_worker_init_db(**_):
        db.init_app(app)

def make_celery(app):
	celery = Celery('nexus_auth', broker=app.config['CELERY_BROKER_URL'])
	celery.conf.update(app.config)
	TaskBase = celery.Task
	class ContextTask(TaskBase):
		abstract = True
		def __call__(self, *args, **kwargs):
			with app.app_context():
				return TaskBase.__call__(self, *args, **kwargs)
	celery.Task = ContextTask
	return celery
