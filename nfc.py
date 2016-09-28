#!/usr/bin/env python
# -*- coding: utf8 -*-
import RPi.GPIO as GPIO
import MFRC522
import signal
from datetime import datetime

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
MIFAREReader = MFRC522.MFRC522()

# Some Pool vars
players = list()
game_on = False
game_timer = None
player_1_reg_time = None
player_2_reg_time = None
card_loops = 0


def reset_game():
    players = list()
    game_on = False
    player_1_reg_time = None
    player_2_reg_time = None
    card_loops = 0


while continue_reading:
    
    # Scan for cards    
    status, TagType = MIFAREReader.MFRC522_Request(MIFAREReader.PICC_REQIDL)

    # If a card is found
    if status == MIFAREReader.MI_OK:
        # print "Card detected"
        pass
    
    # Get the UID of the card
    status, uid = MIFAREReader.MFRC522_Anticoll()

    if status != MIFAREReader.MI_OK:
        card_loops = 0

    # If we have the UID, continue
    else:
        card_loops += 1

        players_count = len(players)
        if uid not in players and players_count < 2:
            players.append(uid)
            if players_count == 1:
                print "Player #1 registered."
                player_1_reg_time = datetime.now()
            if players_count == 2:
                print "Player #2 registered."
                player_2_reg_time = datetime.now()

        if players_count < 2 and (datetime.now() - player_1_reg_time).seconds > 5:
            print "Players removed. Register both players faster."
            reset_game()

        # Never pass this point if players aren't registered
        if players_count < 2:
            continue

        game_timer = datetime.now()
        game_on = True
        print "Both players registered. Game begins..."

        time_elapsed = 0
        if game_timer is not None:
            time_elapsed = (datetime.now() - game_timer).seconds

        if 5 < time_elapsed < 60*60*30:
            print "Player #{} won".format(players.index(uid) + 1)
            print "Game took {} minute(s) and {} second(s)".format(time_elapsed / 60, time_elapsed % 60)
            reset_game()
            print ""
            print "Waiting for new players..."
            print ""
