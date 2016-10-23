from datetime import timedelta
from freezegun import freeze_time
import json
import mock
import os
import shelve
import sys
import unittest

sys.modules['spi'] = mock.MagicMock()
sys.modules['MFRC522'] = mock.MagicMock()
sys.modules['gpiozero'] = mock.MagicMock()

from .. import game as game_module
from .. import poolbot
from . import test_config

LUKASZ_UID = '111-111-111-111'
JAVIMAN_UID = '222-222-222-222'
PHIL_UID = '333-333-333-333'


class TestGame(unittest.TestCase):

    @mock.patch('poolnfc.poolbot._get_poolbot_users')
    @mock.patch('poolnfc.poolbot.config', test_config)
    def setUp(self, mock_users):
        super(TestGame, self).setUp()
        mock_users.return_value = json.loads(open('tests/poolbot_users_api.txt').read())
        poolbot.add_user('lukasz', LUKASZ_UID)
        poolbot.add_user('javiman', JAVIMAN_UID)
        self.game = game_module.Game()
        self.game.reset_button.is_pressed = False

    def tearDown(self):
        os.remove(test_config.DB_FILE_PATH)
        self.game = None

    @mock.patch('poolnfc.poolbot.config', test_config)
    @mock.patch('poolnfc.poolbot._send_message_to_slack')
    @mock.patch.object(game_module.Game, 'read_uid')
    def test_register_first_user_then_do_nothing(
            self,
            mock_get_uid,
            mock_msg_to_slack,
    ):
        mock_get_uid.return_value = LUKASZ_UID
        self.game.main_loop(infinite=False)

        mock_get_uid.return_value = None
        self.game.main_loop(infinite=False)

        self.assertEqual(self.game.players_count, 1)
        self.assertFalse(self.game.game_can_start)
        self.assertEqual(mock_msg_to_slack.call_count, 0)

    @mock.patch('poolnfc.poolbot.config', test_config)
    @mock.patch('poolnfc.poolbot._send_message_to_slack')
    @mock.patch.object(game_module.Game, 'read_uid')
    def test_game_should_reset_if_only_one_user_registered_for_15s(
            self,
            mock_get_uid,
            mock_msg_to_slack,
    ):
        self.assertFalse(self.game.registration_start_time)

        mock_get_uid.return_value = LUKASZ_UID

        self.game.main_loop(infinite=False)

        mock_get_uid.return_value = None
        self.game.main_loop(infinite=False)

        with freeze_time(self.game.registration_start_time + timedelta(seconds=test_config.REGISTRATION_WINDOW + 1)):
            mock_get_uid.return_value = None
            self.game.main_loop(infinite=False)

        self.assertEqual(self.game.players_count, 0)
        self.assertFalse(self.game.game_can_start)
        self.assertEqual(mock_msg_to_slack.call_count, 0)

    @mock.patch('poolnfc.poolbot.config', test_config)
    @mock.patch('poolnfc.poolbot._send_message_to_slack')
    @mock.patch.object(game_module.Game, 'read_uid')
    def test_register_first_user_then_the_second_one(
            self,
            mock_get_uid,
            mock_msg_to_slack,
    ):
        mock_get_uid.return_value = LUKASZ_UID

        self.game.buzzer = mock.MagicMock()
        self.game.main_loop(infinite=False)

        mock_get_uid.return_value = JAVIMAN_UID
        self.game.main_loop(infinite=False)

        mock_get_uid.return_value = None
        self.game.main_loop(infinite=False)

        self.assertEqual(self.game.players_count, 2)
        self.assertTrue(self.game.game_can_start)
        self.assertTrue(self.game.game_on)
        self.assertEqual(self.game.buzzer.beep.call_count, 3)
        self.assertEqual(mock_msg_to_slack.call_count, 1)

    @mock.patch('poolnfc.poolbot.config', test_config)
    @mock.patch('poolnfc.poolbot._send_message_to_slack')
    @mock.patch.object(game_module.Game, 'read_uid')
    @mock.patch('poolnfc.poolbot._get_poolbot_users')
    def test_register_third_user_while_a_game_is_on(
            self,
            mock_users,
            mock_get_uid,
            mock_msg_to_slack,
    ):
        self.assertEqual(self.game.players_count, 0)
        mock_get_uid.return_value = LUKASZ_UID
        self.game.buzzer = mock.MagicMock()
        self.game.main_loop(infinite=False)
        self.assertEqual(self.game.players_count, 1)

        mock_get_uid.return_value = JAVIMAN_UID
        self.game.main_loop(infinite=False)
        self.assertEqual(self.game.players_count, 2)

        self.assertEqual(self.game.players_count, 2)
        self.assertTrue(self.game.game_can_start)
        self.assertTrue(self.game.game_on)
        self.assertEqual(mock_msg_to_slack.call_count, 1)

        # test if a 3rd, not-assigned NFC tag can trigger "game started" message
        mock_get_uid.return_value = PHIL_UID
        self.assertEqual(self.game.players_count, 2)
        self.game.main_loop(infinite=False)
        self.assertEqual(mock_msg_to_slack.call_count, 1)

        # test if a 3rd, known NFC tag can trigger "game started" message
        mock_users.return_value = json.loads(open('tests/poolbot_users_api.txt').read())
        poolbot.add_user('phil', PHIL_UID)
        self.game.main_loop(infinite=False)
        self.assertEqual(mock_msg_to_slack.call_count, 1)

        mock_get_uid.return_value = None
        self.game.main_loop(infinite=False)

        self.assertEqual(self.game.players_count, 2)
        self.assertEqual(self.game.buzzer.beep.call_count, 4)

    @mock.patch('poolnfc.poolbot.config', test_config)
    @mock.patch('poolnfc.poolbot._send_message_to_slack')
    @mock.patch.object(game_module.Game, 'read_uid')
    def test_end_game(
            self,
            mock_get_uid,
            mock_msg_to_slack,
    ):
        self.game.buzzer = mock.MagicMock()
        mock_get_uid.return_value = LUKASZ_UID
        self.game.main_loop(infinite=False)

        mock_get_uid.return_value = JAVIMAN_UID
        self.game.main_loop(infinite=False)

        mock_get_uid.return_value = None
        self.game.main_loop(infinite=False)

        mock_get_uid.return_value = JAVIMAN_UID
        self.game.main_loop(infinite=False)

        self.assertEqual(self.game.players_count, 0)
        self.assertFalse(self.game.game_can_start)
        self.assertFalse(self.game.game_on)

        self.assertEqual(self.game.buzzer.beep.call_count, 4)
        self.assertEqual(mock_msg_to_slack.call_count, 2)

    @mock.patch('poolnfc.poolbot.config', test_config)
    @mock.patch('poolnfc.poolbot._get_poolbot_users')
    @mock.patch('poolnfc.game.raw_input')
    @mock.patch.object(game_module.Game, 'read_uid')
    def test_adding_uid_for_a_new_user(
            self,
            mock_get_uid,
            mock_raw_input,
            mock_users,
    ):
        mock_get_uid.return_value = '444-444-444-444'
        mock_raw_input.return_value = 'matus'
        mock_users.return_value = json.loads(open('tests/poolbot_users_api.txt').read())

        self.game.new_user_loop(infinite=False)

        db = shelve.open(test_config.DB_FILE_PATH)
        self.assertEqual(len(db), 3)

    @mock.patch('poolnfc.poolbot.config', test_config)
    @mock.patch('poolnfc.poolbot._get_poolbot_users')
    @mock.patch('poolnfc.game.raw_input')
    @mock.patch.object(game_module.Game, 'read_uid')
    def test_adding_uid_for_an_existing_user(
        self,
        mock_get_uid,
        mock_raw_input,
        mock_users,
    ):
        mock_get_uid.return_value = '321-321-321-321'
        mock_raw_input.return_value = 'lukasz'
        mock_users.return_value = json.loads(open('tests/poolbot_users_api.txt').read())

        db = shelve.open(test_config.DB_FILE_PATH)
        self.assertEqual(len(db['lukasz']['uids']), 1)
        db.close()

        self.game.new_user_loop(infinite=False)

        db = shelve.open(test_config.DB_FILE_PATH)
        self.assertEqual(len(db['lukasz']['uids']), 2)
        db.close()

    @mock.patch('poolnfc.poolbot.config', test_config)
    @mock.patch('poolnfc.poolbot._get_poolbot_users')
    @mock.patch('poolnfc.game.raw_input')
    @mock.patch.object(game_module.Game, 'read_uid')
    def test_adding_uid_that_is_already_tied_to_another_user(
        self,
        mock_get_uid,
        mock_raw_input,
        mock_users,
    ):
        mock_get_uid.return_value = JAVIMAN_UID
        mock_raw_input.return_value = 'lukasz'
        mock_users.return_value = json.loads(open('tests/poolbot_users_api.txt').read())

        db = shelve.open(test_config.DB_FILE_PATH)
        self.assertEqual(len(db['lukasz']['uids']), 1)
        db.close()

        self.game.new_user_loop(infinite=False)

        db = shelve.open(test_config.DB_FILE_PATH)
        self.assertEqual(len(db['lukasz']['uids']), 1)
        db.close()

    @mock.patch('poolnfc.poolbot.config', test_config)
    @mock.patch('poolnfc.poolbot._get_poolbot_users')
    @mock.patch('poolnfc.game.raw_input')
    @mock.patch.object(game_module.Game, 'read_uid')
    def test_adding_uid_that_is_already_tied_to_the_user(
        self,
        mock_get_uid,
        mock_raw_input,
        mock_users,
    ):
        mock_get_uid.return_value = LUKASZ_UID
        mock_raw_input.return_value = 'lukasz'
        mock_users.return_value = json.loads(open('tests/poolbot_users_api.txt').read())

        db = shelve.open(test_config.DB_FILE_PATH)
        self.assertEqual(len(db['lukasz']['uids']), 1)
        db.close()

        self.game.new_user_loop(infinite=False)

        db = shelve.open(test_config.DB_FILE_PATH)
        self.assertEqual(len(db['lukasz']['uids']), 1)
        db.close()

    @mock.patch('poolnfc.poolbot.config', test_config)
    @mock.patch('poolnfc.poolbot._send_message_to_slack')
    @mock.patch.object(game_module.Game, 'read_uid')
    def test_abandoning_the_game(
            self,
            mock_get_uid,
            mock_msg_to_slack,
    ):
        self.game.buzzer = mock.MagicMock()
        mock_get_uid.return_value = LUKASZ_UID
        self.game.reset_button.is_pressed = False
        self.game.main_loop(infinite=False)

        mock_get_uid.return_value = JAVIMAN_UID
        self.game.main_loop(infinite=False)

        mock_get_uid.return_value = None
        self.game.main_loop(infinite=False)

        self.game.reset_button.is_pressed = True
        self.game.main_loop(infinite=False)

        self.assertEqual(self.game.players_count, 0)
        self.assertFalse(self.game.game_can_start)
        self.assertFalse(self.game.game_on)

        self.assertEqual(self.game.buzzer.beep.call_count, 4)
        self.assertEqual(mock_msg_to_slack.call_count, 2)
