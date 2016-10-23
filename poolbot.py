# -*- coding: utf8 -*-
import json
import shelve

import requests
import slackclient
from time import sleep

import live_config as config


users = None


def _create_session():
    s = requests.Session()
    s.headers.update({
        'Authorization': 'Token {token}'.format(token=config.SERVER_TOKEN)
    })
    return s


def _get_poolbot_users():
    global users
    if users is not None:
        return users

    print "Requesting list of users..."
    s = _create_session()
    users = json.loads(s.get(config.URL_PLAYER).content)
    return users


def send_result_to_server(
    winner_slack_id,
    loser_slack_id,
    granny=False,
):
    """ Sends results of the game to the poolbot server"""
    s = _create_session()

    res = s.post(
        config.URL_MATCH,
        data={
            'winner': winner_slack_id,
            'loser': loser_slack_id,
            'granny': granny,
            'channel': config.POOL_CHANNEL_ID,
        }
    )
    return res.status_code == requests.codes.created


def _send_message_to_slack(msg):
    sc = slackclient.SlackClient(token=config.NFC_BOT_TOKEN)

    for i in xrange(1, 6):
        try:
            res = sc.api_call(
                'chat.postMessage',
                channel=config.POOL_CHANNEL_ID,
                text=msg,
                as_user=True,
            )
            if res.get('ok', False):
                print "Message sent after %d tries" % i
                return

        except Exception, e:  # catch everything
            seconds = 2**i
            print '=== slack request failed (%d) ===' % i
            print "Backing off for %d seconds" % seconds
            print e
            print e.message
            print '================================='

            sleep(seconds)
            continue

    print "Slack request failed after 5 attempts."


def send_game_end_message(
    winner_slack_id,
    loser_slack_id,
    game_time,
    granny=False,
):
    msg = ":nfc-red: <@{}> has won the match against <@{}>. It all took {}".format(
        winner_slack_id,
        loser_slack_id,
        game_time,
    )
    _send_message_to_slack(msg)


def send_game_start_message(
        player_1_slack_id,
        player_2_slack_id,
):
    msg = ":nfc-green: Match between <@{}> and <@{}> started.".format(
        player_1_slack_id,
        player_2_slack_id,
    )
    _send_message_to_slack(msg)


def set_game_abandoned_message():
    _send_message_to_slack("Game has been abandoned.")


def add_user(username, nfc_uid):
    """
    Tie NFC tag's UID(s) with a slack/potato user.
    You can add more than one tag UID per user.
    """
    try:
        users = _get_poolbot_users()
    except ValueError:
        print "Could not retrieve users from the poolbot server."
        return False

    found = filter(lambda x: x['name'] == username, users)
    if not found:
        print "Username '{}' not found on the poolbot server.".format(username)
        return False

    user = found[0]
    db = shelve.open(config.DB_FILE_PATH, writeback=True)
    if username in db:
        # Check this UID isn't registered with another user.
        # Abort with a message if so.
        all_other_users = {usr[0]: usr[1] for usr in db.items() if usr[0] != username}
        found = filter(lambda a: nfc_uid in a[1]['uids'], all_other_users.items())
        if found:
            print nfc_uid
            print "This NFC tag has been already assigned to {}.".format(found[0][0])
            return True

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
    return True


def get_user(nfc_uid):
    """
    Finds and return username/user data pairs from the local db.
    Raises IndexError if user not in the db.
    """
    db = shelve.open(config.DB_FILE_PATH)
    return filter(lambda x: nfc_uid in x['uids'], db.values()).pop()

