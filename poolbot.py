# -*- coding: utf8 -*-
import requests

from config import (
    SERVER_TOKEN,
    URL_MATCH,
    POOL_CHANNEL_ID,
)


def _create_session():
    s = requests.Session()
    s.headers.update({
        'Authorization': 'Token {token}'.format(token=SERVER_TOKEN)
    })
    return s


def send_result(
    winner_id,
    loser_id,
    granny=False,
):
    """ Sends results of the game to the poolbot server"""
    s = _create_session()

    res = s.post(
        URL_MATCH,
        data={
            'winner': winner_id,
            'loser': loser_id,
            'granny': granny,
            'channel': POOL_CHANNEL_ID,
        }
    )
    return res.status_code == requests.codes.created


# TEST THINGS...
# import json
# from config import URL_PLAYER
# send_result('123', '456', granny=False)
# data = json.loads(_create_session().get(URL_PLAYER).content)
# check = [
#     'ID %s has %d and %d games played' % (p['slack_id'], p['total_elo'], p['total_match_count'])
#     for p in data
# ]
# print '\n'.join(check)

