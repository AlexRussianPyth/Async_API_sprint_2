import os

import ecs_logging

LOG_FILENAME = os.getenv('LOG_FILENAME', '/var/log/app/logs.json')
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
DJANGO_LOG_LEVEL = os.getenv('DJANGO_LOG_LEVEL', 'INFO')

LOG_REQUEST_ID_HEADER = "HTTP_X_REQUEST_ID"
LOG_REQUESTS =  bool(os.getenv('LOG_LEVEL', True))

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
       'request_id': {
            '()': 'log_request_id.filters.RequestIDFilter'
        },
    },
    'formatters': {
        'default': {'format': '[%(request_id)s] [%(asctime)s] %(levelname)s in %(module)s: %(message)s'},
        'ecs_logging': {
            '()': ecs_logging.StdlibFormatter,
        },
    },
    'handlers': {
        'default': { 
            'formatter': 'default',
            'class': 'logging.StreamHandler',
            'filters': ['request_id'],
        },
        'web': {
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': '/var/log/app/logs.json',
            'when': 'h',
            'interval': 1, 
            'backupCount': 5,
            'formatter': 'ecs_logging',
            'filters': ['request_id']
        }
    },
    'loggers': {
        'django': {
            'handlers': ['web', 'default'],
            'level': DJANGO_LOG_LEVEL,
            'propagate': True,
        },
        'django.request': {
            'handlers': ['web', 'default'],
            'level': 'INFO',
            'propagate': False,
        },
        'movies.custom': {
            'handlers': ['web', 'default'],
            'level': LOG_LEVEL,
        }
    }
}