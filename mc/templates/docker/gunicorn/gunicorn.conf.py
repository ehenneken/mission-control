import os
 
APP_NAME = os.environ.get('SERVICE', 'generic_service')
LOG_DIR = '/tmp'

bind = "0.0.0.0:80"
workers = 6
worker_class = "eventlet"
max_requests = 200
max_requests_jitter = 15
preload_app = True
chdir = os.path.dirname(__file__)
daemon = False
debug = False
errorlog = '{}/{}.error.log'.format(LOG_DIR, APP_NAME)
accesslog = '{}/{}.access.log'.format(LOG_DIR, APP_NAME)
pidfile = '{}/{}.pid'.format(LOG_DIR, APP_NAME)
loglevel = "info"
