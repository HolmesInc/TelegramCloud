import os
import base64
import pathlib
from json_log_formatter import JSONFormatter
from mongoengine import register_connection
from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from app.errors import StartUpError

###################################################################################################
# Server settings
###################################################################################################
APP_DIR = pathlib.Path(
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
APP_LOG_DIR = os.getenv('APP_LOG_DIR', f'{APP_DIR}/logs/')
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
            '()': 'app.config.CustomisedJSONFormatter',
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
# Bot settings
###################################################################################################
TOKEN = os.getenv('TOKEN', None)
ROOT_DIRECTORY = os.getenv('ROOT_DIRECTORY', 'ROOT')
SECRET_KEY = os.getenv('SECRET_KEY', None)
SALT = os.getenv('SALT', None)
CANCEL_BUTTON = 'Cancel'
DIRECTORY_ACTIONS = {
    'goto': 'goto',
    'delete': 'delete'
}
if not TOKEN:
    raise StartUpError("TOKEN is requires environment variable")

if not SECRET_KEY:
    raise StartUpError("SECRET_KEY is requires environment variable")

if not SALT:
    raise StartUpError("SALT is requires environment variable")

###################################################################################################
# NoSQL DB settings
###################################################################################################
MONGO_USER = os.getenv('MONGO_USER', None)
MONGO_PASSWORD = os.getenv('MONGO_PASSWORD', None)
MONGO_HOST = os.getenv('MONGO_HOST', None)
MONGO_PORT = os.getenv('MONGO_PORT', None)
MONGO_DB_NAME = os.getenv('MONGO_DB_NAME', None)
MONGO_CONNECTION_URL = f'mongodb://{MONGO_USER}:{MONGO_PASSWORD}@{MONGO_HOST}:{MONGO_PORT}/{MONGO_DB_NAME}'
MONGO_ENGINE_ALIAS = 'core'
if not MONGO_USER:
    raise StartUpError("MONGO_USER is requires environment variable")

if not MONGO_PASSWORD:
    raise StartUpError("MONGO_PASSWORD is requires environment variable")

if not MONGO_HOST:
    raise StartUpError("MONGO_HOST is requires environment variable")

if not MONGO_PORT:
    raise StartUpError("MONGO_PORT is requires environment variable")

if not MONGO_DB_NAME:
    raise StartUpError("MONGO_DB_NAME is requires environment variable")

register_connection(alias=MONGO_ENGINE_ALIAS, host=MONGO_CONNECTION_URL)

###################################################################################################
# Cryptography settings
###################################################################################################
__password = SECRET_KEY.encode()
__salt = SALT.encode()
__kdf = PBKDF2HMAC(
    algorithm=hashes.SHA256(),
    length=32,
    salt=__salt,
    iterations=100000,
    backend=default_backend()
)
__key = base64.urlsafe_b64encode(__kdf.derive(__password))

CRYPTO = Fernet(__key)
