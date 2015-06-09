import multiprocessing,os
 
APP_NAME = 'mission-control'
LOG_DIR = 'logs'
PORT = 8081

if not os.path.isdir(LOG_DIR):
  os.makedirs(LOG_DIR)

bind = "0.0.0.0:{}".format(PORT)
workers = 5
max_requests = 200
preload_app = True
chdir = os.path.dirname(__file__)
daemon = False
debug = False
errorlog = '{}/{}.error.log'.format(LOG_DIR, APP_NAME)
accesslog = '{}/{}.access.log'.format(LOG_DIR, APP_NAME)
pidfile = '{}/{}.pid'.format(LOG_DIR, APP_NAME)
loglevel="info"
