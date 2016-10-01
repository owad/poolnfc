#!/usr/bin/env python
# -*- coding: utf8 -*-
import logging
import signal
import sys
from datetime import datetime as dt
from time import sleep

import RPi.GPIO as GPIO

import config
import MFRC522
from beeper import beep
import poolbot


continue_reading = True

LOOP_MODE = config.USER_ADD_MODE if len(sys.argv) > 1 else config.GAME_MODE


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
players = list()
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

    players = list()
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

        if LOOP_MODE == config.USER_ADD_MODE:
            print "=" * 50
            username = raw_input("NFC UID captured. Enter your username: ")
            poolbot.add_user(username, uid)
            continue

        if uid not in players and players_count < 2:
            players.append(uid)
            players_count = len(players)
            username, user_data = poolbot.get_user(uid)
            locals()['player_{}_reg_time'.format(players_count)] = dt.now()
            logging.debug("{} registered.".format(username))
            beep()

        if uid in players and game_timer:  # Only current players are allowed to end the game
            players.remove(uid)
            loser_uid = players.pop()
            winner, winner_data = poolbot.get_user(uid)
            loser, loser_data = poolbot.get_user(loser_uid)

            logging.debug("{} has won a match against {}.".format(winner, loser))
            logging.debug("Game took {} minute(s) and {} second(s)".format(time_elapsed / 60, time_elapsed % 60))

            print
            print "Winner: {}. Slack ID '{}'.".format(winner, winner_data['slack_id'])
            print "Loser: {}. Slack ID '{}'.".format(loser, loser_data['slack_id'])
            print
            # send_result(
            #     winner_data['slack_id'],
            #     loser_data['slack_id'],
            #     granny=False,
            # )
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

    time_elapsed = (dt.now() - game_timer).seconds

