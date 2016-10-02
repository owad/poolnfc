import logging
import os

SERVER_TOKEN = 'a2afc1ad9accf71312833dd4121b6cb47ee6764d'
SERVER_HOST = 'http://192.168.0.19:8000'

URL_MATCH = SERVER_HOST + '/api/match/'
URL_PLAYER = SERVER_HOST + '/api/player/'

POOL_CHANNEL_ID = 'ABC123'

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

