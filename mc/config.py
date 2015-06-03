GITHUB_SIGNATURE_HEADER = 'X-Hub-Signature'
GITHUB_SECRET = 'redacted'

MC_LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'default': {
            'format': '%(levelname)s\t%(process)d '
                      '[%(asctime)s]:\t%(message)s',
            'datefmt': '%m/%d/%Y %H:%M:%S',
        }
    },
    'handlers': {
        'file': {
            'formatter': 'default',
            'level': 'DEBUG',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': '/tmp/app.log',
        },
        'console': {
            'formatter': 'default',
            'level': 'DEBUG',
            'class': 'logging.StreamHandler'
        },
#        'syslog': {
#            'formatter': 'default',
#            'level': 'DEBUG',
#            'class': 'logging.handlers.SysLogHandler',
#            'address': '/dev/log'
#        }
    },
    'loggers': {
        '': {
            'handlers': ['file', 'console'],
            'level': 'CRITICAL',
            'propagate': True,
        },
    },
}

SQLALCHEMY_DATABASE_URI = 'sqlite://'
