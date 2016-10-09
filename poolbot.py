# -*- coding: utf8 -*-
import json
import logging
import os
import shelve

import requests
import slackclient


from config import (
    SERVER_TOKEN,
    URL_MATCH,
    URL_PLAYER,
    POOL_CHANNEL_ID,
    ROOT_PATH,
    NFC_BOT_TOKEN,
)


def _create_session():
    s = requests.Session()
    s.headers.update({
        'Authorization': 'Token {token}'.format(token=SERVER_TOKEN)
    })
    return s


def send_result_to_server(
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


def _send_message_to_slack(msg):
    sc = slackclient.SlackClient(token=NFC_BOT_TOKEN)
    sc.api_call(
        'chat.postMessage',
        channel='#pool',
        text=msg,
        username='zebra',
        as_user=True,
    )


def send_result_to_slack(
    winner_slack_id,
    loser_slack_id,
    game_time,
    granny=False,
):
    msg = ":nfc: <@{}> beat <@{}>. The game took {}".format(
        winner_slack_id,
        loser_slack_id,
        game_time,
    )
    _send_message_to_slack(msg)


def send_game_start_to_slack(
        player_1_slack_id,
        player_2_slack_id,
):
    msg = "Match between <@{}> and <@{}> started.".format(
        player_1_slack_id,
        player_2_slack_id,
    )
    _send_message_to_slack(msg)


def add_user(username, nfc_uid):
    """
    Tie NFC tag's UID(s) with a slack/potato user.
    You can add more than one tag UID per user.
    """
    try:
        s = _create_session()
        data = json.loads(s.get(URL_PLAYER).content)
    except Exception, e:
        print "Could not retrieve users from the poolbot server."
        return

    found = filter(lambda x: x['name'] == username, data)
    if not found:
        print "Username '{}' not found on the poolbot server.".format(username)
        return

    user = found[0]
    db = shelve.open(os.path.join(ROOT_PATH, 'users.db'), writeback=True)

    # Check this UID isn't already registered with a user.
    # Abort with a message if so.
    found = filter(lambda a: nfc_uid in a[1]['uids'], db.items())
    if found:
        print nfc_uid
        print "This NFC tag has been already assigned to {}.".format(found[0][0])
        return

    if username in db:
        db[username]['uids'].add(nfc_uid)
        db[username]['username'] = user['name']  # set it again just in case username has been changed
    else:
        db[username] = {
            'slack_id': user['slack_id'],
            'uids': {nfc_uid},
            'username': user['name'],
        }

    db.close()
    print "This NFC tag has been assigned to {}".format(username)


def get_user(nfc_uid):
    """
    Finds and return username/user data pairs from the local db.
    Raises IndexError if user not in the db.
    """
    db = shelve.open(os.path.join(ROOT_PATH, 'users.db'))
    return filter(lambda x: nfc_uid in x['uids'], db.values()).pop()

