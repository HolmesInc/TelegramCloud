import os
import pathlib
from json_log_formatter import JSONFormatter

###################################################################################################
# Server settings
###################################################################################################
ROOT_DIR = pathlib.Path(
    os.path.abspath(os.path.dirname(__file__))
)
DEBUG_MODE = os.getenv('DEBUG_MODE', True)

###################################################################################################
# Logging
###################################################################################################
APP_LOG_FORMAT = (
    '-' * 80 + '\n' +
    '[%(asctime)s] %(name)s.%(levelname)s in %(funcName)s (%(pathname)s:%(lineno)d):\n' +
    '%(message)s\n' +
    '-' * 80
)
APP_LOG_DIR = os.getenv('APP_LOG_DIR', f'{ROOT_DIR}/logs/')
APP_LOG_PATH = f'{APP_LOG_DIR}telegram_cloud.log'
APP_LOG_FILE_ROTATION_SIZE = int(os.getenv('APP_LOG_FILE_ROTATION_SIZE', 100000))
APP_LOG_FILE_BACKUP_COUNT = int(os.getenv('APP_LOG_FILE_BACKUP_COUNT', 14))
APP_LOG_LEVEL = os.getenv('APP_LOG_LEVEL', 'WARNING') if not DEBUG_MODE else 'DEBUG'
if not os.path.exists(APP_LOG_DIR):
    os.makedirs(APP_LOG_DIR)


class CustomisedJSONFormatter(JSONFormatter):
    """ Re-configure standard logger to have JSON-like log messages
    """
    def json_record(self, message, extra, record):
        super(CustomisedJSONFormatter, self).json_record(message, extra, record)
        if "ERROR" in record.levelname:
            extra['status'] = "ERROR"
        else:
            extra['status'] = record.levelname
        extra['message'] = message
        extra['function'] = getattr(record, 'funcName', 'unknown')
        extra['path'] = getattr(record, 'pathname', 'unknown')
        return extra


LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'default': {
            'format': APP_LOG_FORMAT,
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
        'custom': {
            '()': 'config.CustomisedJSONFormatter',
        }
    },
    'handlers': {
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': APP_LOG_PATH,
            'maxBytes': APP_LOG_FILE_ROTATION_SIZE,
            'backupCount': APP_LOG_FILE_BACKUP_COUNT,
            'formatter': 'custom',
        },
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'custom',
        },
    },
    'loggers': {
        'telegram_cloud': {
            'handlers': ['console', 'file'],
            'level': APP_LOG_LEVEL,
        },
    }
}

###################################################################################################
#
###################################################################################################
