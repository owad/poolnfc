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
game_start_time = None
last_card = None
first_registered = None

PLAYER_2_WAIT_TIME = 5

# This loop keeps checking for chips. If one is near it will get the UID and authenticate
while continue_reading:
    
    # Scan for cards    
    status, TagType = MIFAREReader.MFRC522_Request(MIFAREReader.PICC_REQIDL)

    # If a card is found
    if status == MIFAREReader.MI_OK:
        # print "Card detected"
        pass
    
    # Get the UID of the card
    status, uid = MIFAREReader.MFRC522_Anticoll()

    # If we have the UID, continue
    if status == MIFAREReader.MI_OK:

        # print "UID: ", '-'.join(uid)

        if uid not in players and len(players) < 2:  # do not add players if there's already two
            players.append(uid)

        # # This is the default key for authentication
        # key = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]
        #
        # # Select the scanned tag
        # MIFAREReader.MFRC522_SelectTag(uid)
        #
        # # Authenticate
        # status = MIFAREReader.MFRC522_Auth(MIFAREReader.PICC_AUTHENT1A, 8, key, uid)
        #
        # # Check if authenticated
        # if status == MIFAREReader.MI_OK:
        #     MIFAREReader.MFRC522_Read(8)
        #     MIFAREReader.MFRC522_StopCrypto1()
        # else:
        #     print "Authentication error"
        #
        # print ""

        # Start the timer (PLAYER_2_WAIT_TIME) if the 1st player registers
        if len(players) == 1:
            first_registered = datetime.now()
            print "Player #1 registered. Waiting for players 2..."

        # Reset the players list if 2nd player haven't registered
        # within the PLAYER_2_WAIT_TIME seconds after player #1 registered
        if first_registered and (datetime.now() - first_registered).seconds > PLAYER_2_WAIT_TIME and len(players) < 2:
            players = list()
            print "Player #2 did not register on time (%d seconds passed). Resetting..." % PLAYER_2_WAIT_TIME

        # Begin the game (game_on) and start the game time (time_elapsed)
        # if both players registered within the given time
        if len(players) == 2 and game_on is False:
            game_start_time = datetime.now()
            game_on = True
            print "Both players registered. Game begins..."

        time_elapsed = 0
        if game_start_time is not None:
            time_elapsed = (datetime.now() - game_start_time).seconds

        if PLAYER_2_WAIT_TIME < time_elapsed < 60*60*30:
            print "Player #{} won".format(players.index(uid) + 1)
            print "Game took {} minute(s) and {} second(s)".format(time_elapsed/60, time_elapsed%60)
            game_on = False
            players = list()
            first_registered = None
            game_start_time = None
            print ""
            print "Waiting for new players..."
            print ""
