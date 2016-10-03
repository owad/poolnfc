import logging
import os

SERVER_TOKEN = '123'
SERVER_HOST = 'https://test.com'

URL_MATCH = SERVER_HOST + '/api/match/'
URL_PLAYER = SERVER_HOST + '/api/player/'

POOL_CHANNEL_ID = 'C123'

ROOT_PATH = '/home/pi/Workspace/poolnfc'

LOGGER_CONFIG = {
    'filename': os.path.join(ROOT_PATH, 'games.log'),
    'format': '%(asctime)s %(levelname)s: %(message)s',
    'datefmt': '%Y-%d-%m %I:%M:%S %p',
    'level': logging.DEBUG,
}

# loop modes
GAME_MODE = 'game'
USER_ADD_MODE = 'user_add'


logging.basicConfig(**LOGGER_CONFIG)

NFC_BOT_TOKEN = '123123123'  # London
