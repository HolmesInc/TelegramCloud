from logging import getLogger
from logging.config import dictConfig
from config import LOGGING_CONFIG

dictConfig(LOGGING_CONFIG)
logger = getLogger('telegram_cloud')
