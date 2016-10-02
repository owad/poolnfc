# -*- coding: utf8 -*-
import json
import logging
import os

import requests
import shelve

from config import (
    SERVER_TOKEN,
    URL_MATCH,
    URL_PLAYER,
    POOL_CHANNEL_ID,
    ROOT_PATH,
)


def _create_session():
    s = requests.Session()
    s.headers.update({
        'Authorization': 'Token {token}'.format(token=SERVER_TOKEN)
    })
    return s


def send_result(
    winner_slack_id,
    loser_slack_id,
    granny=False,
):
    """ Sends results of the game to the poolbot server"""
    s = _create_session()

    res = s.post(
        URL_MATCH,
        data={
            'winner': winner_slack_id,
            'loser': loser_slack_id,
            'granny': granny,
            'channel': POOL_CHANNEL_ID,
        }
    )
    return res.status_code == requests.codes.created


def add_user(username, nfc_uid):
    """
    Tie NFC tag's UID(s) with a slack/potato user.
    You can add more than one tag UID per user.
    """
    db = shelve.open(os.path.join(ROOT_PATH, 'users.db'), writeback=True)
    if username in db:
        # Check this UID isn't registered with another user.
        # Abort with a message if so.
        all_other_users = {usr[0]: usr[1] for usr in db.items() if usr[0] != username}
        found = filter(lambda a: nfc_uid in a[1]['uids'], all_other_users.items())
        if found:
            msg = "This NFC tag has been already assigned to {}.".format(found[0][0])
            logging.warning(nfc_uid)
            logging.warning(msg)
            print msg
            return

        db[username]['uids'].add(nfc_uid)

    else:
        try:
            s = _create_session()
            data = json.loads(s.get(URL_PLAYER).content)
        except Exception, e:
            msg = "Could not retrieve users from the poolbot server."
            logging.exception(msg)
            logging.exception(e)
            print msg
            return

        found = filter(lambda x: x['name'] == username, data)
        if not found:
            msg = "Username '{}' not found on the poolbot server.".format(username)
            logging.error(msg)
            print msg
            return

        user = found[0]

        db[username] = {
            'slack_id': user['slack_id'],
            'uids': {nfc_uid},
        }

    db.close()
    msg = "This NFC tag has been assigned to {}".format(username)
    logging.debug(msg)
    print msg


def get_user(nfc_uid):
    """
    Finds and return username/user data pairs from the local db.
    Raises IndexError if user not in the db.
    """
    db = shelve.open(os.path.join(ROOT_PATH, 'users.db'))
    return filter(lambda usr: nfc_uid in usr[1]['uids'], db.items()).pop()

