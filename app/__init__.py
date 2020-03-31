from logging import getLogger
from logging.config import dictConfig
from . import config

dictConfig(config.LOGGING_CONFIG)
logger = getLogger('telegram_cloud')
