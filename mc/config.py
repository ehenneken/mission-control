GITHUB_SIGNATURE_HEADER = 'X-Hub-Signature'
GITHUB_SECRET = 'redacted'
GITHUB_COMMIT_API = 'https://api.github.com/repos/adsabs/{repo}/git/commits/{hash}'
GITHUB_TAG_FIND_API = 'https://api.github.com/repos/adsabs/{repo}/git/refs/tags/{tag}'
GITHUB_TAG_GET_API = 'https://api.github.com/repos/adsabs/{repo}/git/tags/{hash}'
AWS_REGION = 'us-east-1'
AWS_ACCESS_KEY = 'redacted'
AWS_SECRET_KEY = 'redacted'

WATCHED_REPOS = [
    'adsws',
    'solr-service',
    'export_service',
    'graphics_service',
    'recommender_service',
    'citation_helper_service',
    'metrics_service',
    'vis-services',
    'biblib-service',
    'orcid-service',
    'myads',
    'object_search'
]

# Local dependencies for the testing environment
DOCKER_BRIDGE = '172.17.42.1'
DEPENDENCIES = {
    'POSTGRES': {
        'USERNAME': 'postgres',
        'PORT': 5432,
        'HOST': 'localhost',
        'IMAGE': 'postgres:9.3'
    },
    'CONSUL': {
        'PORT': 8500,
        'IMAGE': 'adsabs/consul:v1.0.0'
    },
    'REDIS': {
        'PORT': 6379,
        'IMAGE': 'redis:2.8.21'
    },
    'GUNICORN': {
        'PORT': 80
    },
    'REGISTRATOR': {
        'IMAGE': 'gliderlabs/registrator:latest'
    },
    'SOLR': {
        'PORT': 8983,
        'IMAGE': 'adsabs/montysolr:v48.1.0.3'
    }
}

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
        'console': {
            'formatter': 'default',
            'level': 'DEBUG',
            'class': 'logging.StreamHandler'
        },
    },
    'loggers': {
        '': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}

SQLALCHEMY_DATABASE_URI = 'sqlite://'
SQLALCHEMY_TRACK_MODIFICATIONS = False
