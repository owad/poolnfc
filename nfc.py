#!/usr/bin/env python
# -*- coding: utf8 -*-
from datetime import datetime as dt, timedelta
import logging
import RPi.GPIO as GPIO
import signal
import sys

from beeper import beep
import MFRC522
import poolbot


# Capture SIGINT for cleanup when the script is aborted
def end_read(signal, frame):
    global continue_reading
    continue_reading = False
    GPIO.cleanup()


# Hook the SIGINT
signal.signal(signal.SIGINT, end_read)


class Game(object):

    def __init__(self):
        self.players = dict()
        self.timer = None
        self.nfc_reader = MFRC522.MFRC522()

    @property
    def players_count(self):
        return len(self.players)

    @property
    def time_elapsed(self):
        if self.timer is None:
            return 0
        return (dt.now() - self.timer).seconds

    @property
    def game_on(self):
        return bool(self.timer)

    def game_can_start(self):
        return self.players_count == 2

    def reset(self):
        logging.debug("Resetting the game. Register both players faster (within 15 seconds).")
        self.players = dict()
        self.timer = None

    def read_uid(self):
        """
        Checks if NFC tag is available (within the reader's sight)
        :return: uid (or None)
        """
        reader_status, reader_uid = self.nfc_reader.MFRC522_Anticoll()
        if reader_status == self.nfc_reader.MI_OK:
            return '-'.join(map(str, reader_uid))
        return None

    def should_reset(self):
        return self.time_elapsed > 15 and self.players_count < 2

    def new_users_loop(self, infinite=True):
        keep_going = True
        while keep_going:
            keep_going = infinite

            tag_uid = self.read_uid()
            if tag_uid:
                print "=" * 50
                user_name = raw_input("NFC UID captured. Enter your username: ")
                poolbot.add_user(user_name, tag_uid)
                continue

            if not infinite:
                break

    def game_loop(self, infinite=True):

        keep_going = True
        while keep_going:
            keep_going = infinite
            tag_uid = self.read_uid()

            try:
                user_data = poolbot.get_user(tag_uid)
            except IndexError:  # raised when tag_uid is None or user doesn't exist
                logging.debug("NFC tag not tied with any user.")
                continue

            if self.players_count < 2 and tag_uid not in self.players:
                self.players[tag_uid] = user_data
                logging.debug("{} registered.".format(user_data['username']))
                beep()

            if self.game_on and tag_uid in self.players:  # winner known
                winner_data = self.players.pop(tag_uid)
                loser_data = self.players.values()[0]

                logging.debug("{} has won a match against {}.".format(
                    winner_data['username'],
                    loser_data['username'],
                ))
                logging.debug("Game took {}".format(str(timedelta(seconds=self.time_elapsed))))

                poolbot.send_result_to_slack(
                    winner_data['slack_id'],
                    loser_data['slack_id'],
                    str(timedelta(seconds=self.time_elapsed)),
                )

                beep(beeps=2, length=2)
                self.reset()
                logging.debug("====== GAME OVER ======")

            if self.should_reset():
                self.reset()

            if self.game_can_start():
                self.timer = dt.now()
                poolbot.send_game_start_to_slack(
                    *[usr['slack_id'] for usr in self.players.values()]
                )
                beep(length=3)


if __name__ == "__main__":
    game = Game()
    if 'add_user' in sys.argv:
        game.new_users_loop()
    else:
        game.game_loop()
