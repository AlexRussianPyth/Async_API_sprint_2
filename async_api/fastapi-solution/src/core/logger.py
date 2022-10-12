import os

import ecs_logging
from asgi_correlation_id.context import correlation_id
from asgi_correlation_id.log_filters import CorrelationIdFilter, _trim_string

LOG_FILENAME = os.getenv('LOG_FILENAME', '/var/log/app/logs.json')
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_DEFAULT_HANDLERS = ['console', 'web', 'default']

class RequestIdFilter(CorrelationIdFilter):
    def filter(self, record) -> bool:
        """
        Attach a request ID to the log record.
        """
        cid = correlation_id.get()
        record.request_id = _trim_string(cid, self.uuid_length)
        return True


LOGGING = {
    'version': 1,
    'filters': {
        'request_id': {
            '()': RequestIdFilter,
            'uuid_length': 32,
        },
    },
    'formatters': {
        'default': {
            '()': 'uvicorn.logging.DefaultFormatter',
            'fmt': '%(request_id)s %(levelprefix)s %(message)s',
            'use_colors': None,
        },
        'access': {
            '()': 'uvicorn.logging.AccessFormatter',
            'fmt': "%(request_id)s %(levelprefix)s %(client_addr)s - '%(request_line)s' %(status_code)s",
        },
        'ecs_logging': {
            '()': ecs_logging.StdlibFormatter,
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'default',
            'filters': ['request_id'],
        },
        'default': {
            'formatter': 'default',
            'class': 'logging.StreamHandler',
            'filters': ['request_id'],
        },
        'web': {
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': LOG_FILENAME,
            'when': 'h',
            'interval': 1,
            'backupCount': 5,
            'formatter': 'ecs_logging',
            'filters': ['request_id']
        },
        'access': {
            'formatter': 'access',
            'class': 'logging.StreamHandler',
            'stream': 'ext://sys.stdout',
            'filters': ['request_id'],
        },
    },
    'loggers': {
        '': {
            'handlers': LOG_DEFAULT_HANDLERS,
            'level': 'INFO',
        },
        'uvicorn.error': {
            'level': 'INFO',
        },
        'uvicorn.access': {
            'handlers': ['access', 'web'],
            'level': 'INFO',
            'propagate': False,
        },
    },
    'root': {
        'level': LOG_LEVEL,
        'handlers': LOG_DEFAULT_HANDLERS
    }
}
