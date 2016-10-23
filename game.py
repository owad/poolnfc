#!/usr/bin/env python
# -*- coding: utf8 -*-
from datetime import datetime as dt, timedelta
import logging
from RPi import GPIO
import signal
import sys

import gpiozero
import MFRC522
nfc_reader = MFRC522.MFRC522()

import poolbot


continue_reading = True


GREEN_LED_PIN = 12
BUZZER_PIN = 21
MODE_BUTTON_PIN = 16
RED_LED_PIN = 14


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
        self.start_time = None
        self.registration_start_time = None
        self.red_led = gpiozero.LED(RED_LED_PIN)
        self.green_led = gpiozero.LED(GREEN_LED_PIN)
        self.reset_button = gpiozero.Button(MODE_BUTTON_PIN)
        self.buzzer = gpiozero.Buzzer(BUZZER_PIN)

    @property
    def players_count(self):
        return len(self.players)

    @property
    def time_elapsed(self):
        if self.start_time is None:
            return 0
        return (dt.now() - self.start_time).seconds

    @property
    def game_on(self):
        return bool(self.start_time)

    @property
    def game_can_start(self):
        return self.players_count == 2

    def uid_belongs_to_current_player(self, tag_uid):
        uid_sets = map(
            lambda p: p['uids'],
            self.players.values(),
        )
        players_uids = reduce(
            lambda x, y: x | y,
            uid_sets,
        )
        return tag_uid in players_uids

    def reset(self):
        logging.debug("Resetting the game. Register both players faster (within 15 seconds).")
        self.players = {}
        self.start_time = None
        self.registration_start_time = None

    def read_uid(self):
        """
        Checks if NFC tag is available (within the reader's sight)
        :return: uid (or None)
        """
        nfc_reader.MFRC522_Request(nfc_reader.PICC_REQIDL)
        reader_status, reader_uid = nfc_reader.MFRC522_Anticoll()
        if reader_status == nfc_reader.MI_OK:
            return '-'.join(map(str, reader_uid))
        return None

    def should_reset(self):
        if not self.registration_start_time:
            return False

        seconds_since_reg_started = (dt.now() - self.registration_start_time).seconds
        return seconds_since_reg_started > poolbot.config.REGISTRATION_WINDOW and self.players_count < 2

    def new_user_loop(self, infinite=True):
        keep_going = True
        while keep_going:
            keep_going = infinite and continue_reading
            user_added = False
            tag_uid = self.read_uid()

            self.buzzer.beep(on_time=0.1, off_time=0.1, n=1)
            if tag_uid:
                print "NFC UID captured."
                while not user_added:

                    print "=" * 50
                    user_name = raw_input("Enter your username: ")
                    user_added = poolbot.add_user(user_name, tag_uid)
                    if user_added:
                        print "User added successfully."
                        break

                    if user_name == '':
                        break

    def main_loop(self, infinite=True):

        keep_going = True
        while keep_going:
            keep_going = infinite and continue_reading
            tag_uid = self.read_uid()

            if self.should_reset():
                self.reset()
                self.buzzer.beep(on_time=0.1, off_time=0.1, n=5)

            if self.reset_button.is_pressed:
                self.reset()
                self.buzzer.beep(on_time=0.1, off_time=0.1, n=5)
                poolbot.set_game_abandoned_message()

            try:
                user_data = poolbot.get_user(tag_uid)
            except IndexError:  # raised when tag_uid is None or user doesn't exist
                if tag_uid:
                    logging.debug("NFC tag (%s) not recognised or tied with any user." % tag_uid)
                    self.buzzer.beep(on_time=0.1, off_time=0.1, n=2)
                continue

            if self.players_count < 2 and tag_uid not in self.players:
                self.registration_start_time = dt.now()
                self.players[tag_uid] = user_data
                logging.debug("{} registered.".format(user_data['username']))
                self.buzzer.beep(on_time=0.1, off_time=0.1, n=1)

            if self.game_on and tag_uid in self.players:  # winner known
                winner_data = self.players.pop(tag_uid)
                loser_data = self.players.values()[0]

                logging.debug("{} has won a match against {}.".format(
                    winner_data['username'],
                    loser_data['username'],
                ))
                logging.debug("Game took {}".format(str(timedelta(seconds=self.time_elapsed))))

                self.buzzer.beep(on_time=0.5, off_time=0.2, n=2)
                poolbot.send_game_end_message(
                    winner_data['slack_id'],
                    loser_data['slack_id'],
                    str(timedelta(seconds=self.time_elapsed)),
                )

                self.reset()
                logging.debug("====== GAME OVER ======")

            if self.game_can_start and self.uid_belongs_to_current_player(tag_uid):
                self.buzzer.beep(on_time=0.5, off_time=0.2, n=1)
                self.start_time = dt.now()
                poolbot.send_game_start_message(
                    *[usr['slack_id'] for usr in self.players.values()]
                )


if __name__ == "__main__":
    game = Game()
    game.green_led.on()

    if 'new_user' in sys.argv:
        game.new_user_loop()

    game.main_loop()
