#!/usr/bin/env python
# -*- coding: utf8 -*-
import logging
import signal
from datetime import datetime as dt
from time import sleep

import RPi.GPIO as GPIO

import MFRC522
from beeper import beep

continue_reading = True

logging.basicConfig(
    filename='games.log',
    format='%(asctime)s %(message)s',
    datefmt='%Y-%d-%m %I:%M:%S %p',
    level=logging.DEBUG,
)


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
        logging.debug("UID: {}".format(uid))

        if uid not in players and players_count < 2:
            players.append(uid)
            players_count = len(players)
            logging.debug("Player #{} registered.".format(players_count))  # TODO: use slack names
            locals()['player_{}_reg_time'.format(players_count)] = dt.now()
            beep()

        if uid in players:  # Only current players are allowed to end the game
            if game_timer and time_elapsed > 10:
                winner = players.index(uid)
                logging.debug("Player #{} won".format(winner + 1))  # TODO: use slack names
                logging.debug("Game took {} minute(s) and {} second(s)".format(time_elapsed / 60, time_elapsed % 60))
                # send_result(  # TODO: use slack user IDs
                #     players.pop(winner),  # winner
                #     players.pop(),  # loser
                #     granny=False,
                # )
                beep(beeps=1, length=3)
                reset_game(sound=False)
                logging.debug("Waiting for new players...")
                sleep(5)

    if player_1_reg_time and players_count < 2 and (dt.now() - player_1_reg_time).seconds > 5:
        logging.debug("Players removed. Register both players faster.")
        reset_game()

    # Never go past this point if players haven't registered
    if players_count < 2:
        continue

    if game_timer is None:
        logging.debug("Players registered. Game begins!")
        game_timer = dt.now()

    time_elapsed = (dt.now() - game_timer).seconds

