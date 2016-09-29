#!/usr/bin/env python
# -*- coding: utf8 -*-
import RPi.GPIO as GPIO
import MFRC522
import signal
from datetime import datetime as dt
from time import sleep

from poolbot import send_result
from beeper import beep
continue_reading = True


# Capture SIGINT for cleanup when the script is aborted
def end_read(signal, frame):
    global continue_reading
    print "Ctrl+C captured, ending read."
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


def reset_game(sound=True):
    global players
    global game_timer
    global player_1_reg_time
    global player_2_reg_time

    players = list()
    game_timer = None
    player_1_reg_time = None
    player_2_reg_time = None

    if sound:
        beep(beeps=3)


while continue_reading:
    
    # Scan for cards    
    status, TagType = nfc_reader.MFRC522_Request(nfc_reader.PICC_REQIDL)

    # Get the UID of the card
    status, uid = nfc_reader.MFRC522_Anticoll()

    if status == nfc_reader.MI_OK:

        players_count = len(players)
        if uid not in players and players_count < 2:
            players.append(uid)
            beep()
            if players_count == 1:
                print "Player #1 registered."  # TODO: use slack names
                player_1_reg_time = dt.now()
            if players_count == 2:
                print "Player #2 registered."  # TODO: use slack names
                player_2_reg_time = dt.now()

        if players_count < 2 and (dt.now() - player_1_reg_time).seconds > 5:
            print "Players removed. Register both players faster."
            reset_game()

        # Never go past this point if players haven't registered
        if players_count < 2:
            continue
        else:
            print "Players registered. Game begins!"
            game_timer = dt.now()

        time_elapsed = (dt.now() - game_timer).seconds

        if time_elapsed > 10:
            winner = players.index(uid)
            print "Player #{} won".format(winner + 1)  # TODO: replace with the users's slack name
            print "Game took {} minute(s) and {} second(s)".format(time_elapsed / 60, time_elapsed % 60)
            # TODO: post to the poolbot-server, winner/loser values should be slack user IDs
            send_result(
                players.pop(winner),  # winner
                players.pop(),  # loser
                granny=False,
            )
            beep(beeps=1, length=2)
            reset_game(sound=False)
            print ""
            print "Waiting for new players..."
            print ""
            sleep(5)
