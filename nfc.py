#!/usr/bin/env python
# -*- coding: utf8 -*-
import logging
import signal
import sys
from datetime import datetime as dt, timedelta
from time import sleep

import RPi.GPIO as GPIO

import config
import MFRC522
from beeper import beep
import poolbot


continue_reading = True

loop_mode = config.USER_ADD_MODE if len(sys.argv) > 1 and sys.argv[1] != 'start' else config.GAME_MODE


# Capture SIGINT for cleanup when the script is aborted
def end_read(signal, frame):
    global continue_reading
    logging.debug("Ctrl+C captured, ending read.")
    continue_reading = False
    GPIO.cleanup()


# Hook the SIGINT
signal.signal(signal.SIGINT, end_read)

# Create an object of the class MFRC522
nfc_reader = MFRC522.MFRC522()

# Some Pool vars
players = dict()
game_timer = None
player_1_reg_time = None
player_2_reg_time = None
players_count = 0


def reset_game(sound=True):
    global players
    global game_timer
    global player_1_reg_time
    global player_2_reg_time
    global players_count

    players = dict()
    game_timer = None
    player_1_reg_time = None
    player_2_reg_time = None
    players_count = 0

    if sound:
        beep(beeps=3)


while continue_reading:

    # Scan for cards
    status, TagType = nfc_reader.MFRC522_Request(nfc_reader.PICC_REQIDL)

    # Get the UID of the card
    status, uid = nfc_reader.MFRC522_Anticoll()

    if status == nfc_reader.MI_OK:
        uid = '-'.join(map(str, uid))

        logging.debug("UID: {}".format(uid))

        if loop_mode == config.USER_ADD_MODE:
            print "=" * 50
            username = raw_input("NFC UID captured. Enter your username: ")
            poolbot.add_user(username, uid)
            continue

        if uid not in players and players_count < 2:
            try:
                user_data = poolbot.get_user(uid)
            except IndexError:
                logging.debug("NFC tag not tied with any user.")
                continue

            user_data = poolbot.get_user(uid)
            players[uid] = user_data

            players_count = len(players)
            locals()['player_{}_reg_time'.format(players_count)] = dt.now()
            logging.debug("{} registered.".format(user_data['username']))
            beep()

        if uid in players and game_timer:  # Only current players are allowed to end the game
            winner_data = players.pop(uid)
            loser_data = players.values()[0]

            logging.debug("{} has won a match against {}.".format(winner_data['username'], loser_data['username']))
            logging.debug("Game took {}".format(str(timedelta(seconds=time_elapsed))))

            poolbot.send_result_to_slack(
                winner_data['slack_id'],
                loser_data['slack_id'],
                timedelta(seconds=time_elapsed),
            )

            beep(beeps=2, length=2)
            reset_game(sound=False)
            logging.debug("====== GAME OVER ======")
            logging.debug("")
            sleep(5)

    if player_1_reg_time and players_count < 2 and (dt.now() - player_1_reg_time).seconds > 15:
        logging.debug("Resetting the game. Register both players faster (within 15 seconds).")
        reset_game()

    # Never go past this point if players haven't registered
    if players_count < 2:
        continue

    if game_timer is None:
        logging.debug("Players registered. Game begins!")
        beep(length=3)
        game_timer = dt.now()
        poolbot.send_game_start_to_slack(
            *[p['slack_id'] for p in players.values()]
        )

    time_elapsed = (dt.now() - game_timer).seconds

