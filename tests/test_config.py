import os

from ..config import *

SERVER_TOKEN = '1234567890'
SERVER_HOST = 'https://test-app.appspot.com'
#
URL_MATCH = SERVER_HOST + '/api/match/'
URL_PLAYER = SERVER_HOST + '/api/player/'
#
POOL_CHANNEL_ID = 'C123456'
POOLBOT_ID = 'U123456'

ROOT_PATH = '.'
DB_FILE_PATH = os.path.join(ROOT_PATH, 'users.db')

LOGGER_CONFIG = {
    'filename': os.path.join(ROOT_PATH, 'games.log'),
    'format': '%(asctime)s %(levelname)s: %(message)s',
    'datefmt': '%Y-%d-%m %I:%M:%S %p',
    'level': logging.DEBUG,
}

# loop modes
GAME_MODE = 'game'
USER_ADD_MODE = 'user_add'


# logging.basicConfig(**LOGGER_CONFIG)

NFC_BOT_TOKEN = '123abcABC'  # London
