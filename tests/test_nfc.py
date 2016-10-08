import json
import mock
import os
import shelve
import sys
import unittest

sys.modules['spi'] = mock.MagicMock()
sys.modules['MFRC522'] = mock.MagicMock()

from .. import nfc
from .. import poolbot
from . import test_config

LUKASZ_UID = '111-111-111-111'
JAVIMAN_UID = '222-222-222-222'
PHIL_UID = '333-333-333-333'


class TestNFC(unittest.TestCase):

    @mock.patch('poolnfc.poolbot._get_poolbot_users')
    @mock.patch('poolnfc.poolbot.config', test_config)
    def setUp(self, mock_users):
        super(TestNFC, self).setUp()
        mock_users.return_value = json.loads(open('tests/poolbot_users_api.txt').read())
        poolbot.add_user('lukasz', LUKASZ_UID)
        poolbot.add_user('javiman', JAVIMAN_UID)

    def tearDown(self):
        os.remove(test_config.DB_FILE_PATH)

    @mock.patch('poolnfc.poolbot.config', test_config)
    @mock.patch('poolnfc.poolbot._send_message_to_slack')
    @mock.patch.object(nfc.Game, 'read_uid')
    def test_register_first_user_then_do_nothing(
            self,
            mock_get_uid,
            mock_msg_to_slack,
    ):
        game = nfc.Game()

        mock_get_uid.return_value = LUKASZ_UID
        game.game_loop(infinite=False)

        mock_get_uid.return_value = None
        game.game_loop(infinite=False)

        self.assertEqual(game.players_count, 1)
        self.assertFalse(game.game_can_start())
        self.assertEqual(mock_msg_to_slack.call_count, 0)

    @mock.patch('poolnfc.poolbot.config', test_config)
    @mock.patch('poolnfc.poolbot._send_message_to_slack')
    @mock.patch.object(nfc.Game, 'read_uid')
    @mock.patch('poolnfc.nfc.beep')
    def test_register_first_user_then_the_second_one(
            self,
            mock_beep,
            mock_get_uid,
            mock_msg_to_slack,
    ):
        game = nfc.Game()

        mock_get_uid.return_value = LUKASZ_UID
        game.game_loop(infinite=False)

        mock_get_uid.return_value = JAVIMAN_UID
        game.game_loop(infinite=False)

        mock_get_uid.return_value = None
        game.game_loop(infinite=False)

        self.assertEqual(game.players_count, 2)
        self.assertTrue(game.game_can_start())
        self.assertTrue(game.game_on)
        self.assertEqual(mock_beep.call_count, 3)
        self.assertEqual(mock_msg_to_slack.call_count, 1)

    @mock.patch('poolnfc.poolbot.config', test_config)
    @mock.patch('poolnfc.poolbot._send_message_to_slack')
    @mock.patch.object(nfc.Game, 'read_uid')
    @mock.patch('poolnfc.nfc.beep')
    def test_register_third_user_while_a_game_is_on(
            self,
            mock_beep,
            mock_get_uid,
            mock_msg_to_slack,
    ):
        game = nfc.Game()
        self.assertEqual(game.players_count, 0)

        mock_get_uid.return_value = LUKASZ_UID
        game.game_loop(infinite=False)
        self.assertEqual(game.players_count, 1)

        mock_get_uid.return_value = JAVIMAN_UID
        game.game_loop(infinite=False)
        self.assertEqual(game.players_count, 2)

        mock_get_uid.return_value = PHIL_UID
        self.assertEqual(game.players_count, 2)

        game.game_loop(infinite=False)
        mock_get_uid.return_value = None

        game.game_loop(infinite=False)

        self.assertEqual(game.players_count, 2)
        self.assertTrue(game.game_can_start())
        self.assertTrue(game.game_on)
        self.assertEqual(mock_beep.call_count, 3)
        self.assertEqual(mock_msg_to_slack.call_count, 1)

    @mock.patch('poolnfc.poolbot.config', test_config)
    @mock.patch('poolnfc.poolbot._send_message_to_slack')
    @mock.patch.object(nfc.Game, 'read_uid')
    @mock.patch('poolnfc.nfc.beep')
    def test_end_game(
            self,
            mock_beep,
            mock_get_uid,
            mock_msg_to_slack,
    ):
        game = nfc.Game()

        mock_get_uid.return_value = LUKASZ_UID
        game.game_loop(infinite=False)

        mock_get_uid.return_value = JAVIMAN_UID
        game.game_loop(infinite=False)

        mock_get_uid.return_value = None
        game.game_loop(infinite=False)

        mock_get_uid.return_value = JAVIMAN_UID
        game.game_loop(infinite=False)

        self.assertEqual(game.players_count, 0)
        self.assertFalse(game.game_can_start())
        self.assertFalse(game.game_on)
        self.assertEqual(mock_beep.call_count, 4)
        self.assertEqual(mock_msg_to_slack.call_count, 2)

    @mock.patch('poolnfc.poolbot.config', test_config)
    @mock.patch('poolnfc.poolbot._get_poolbot_users')
    @mock.patch('poolnfc.nfc.raw_input')
    @mock.patch.object(nfc.Game, 'read_uid')
    def test_adding_uid_for_a_new_user(
            self,
            mock_get_uid,
            mock_raw_input,
            mock_users,
    ):
        mock_get_uid.return_value = '444-444-444-444'
        mock_raw_input.return_value = 'matus'
        mock_users.return_value = json.loads(open('tests/poolbot_users_api.txt').read())

        game = nfc.Game()
        game.new_users_loop(infinite=False)

        db = shelve.open(test_config.DB_FILE_PATH)
        self.assertEqual(len(db), 3)

    @mock.patch('poolnfc.poolbot.config', test_config)
    @mock.patch('poolnfc.poolbot._get_poolbot_users')
    @mock.patch('poolnfc.nfc.raw_input')
    @mock.patch.object(nfc.Game, 'read_uid')
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

        game = nfc.Game()
        game.new_users_loop(infinite=False)

        db = shelve.open(test_config.DB_FILE_PATH)
        self.assertEqual(len(db['lukasz']['uids']), 2)
        db.close()

    @mock.patch('poolnfc.poolbot.config', test_config)
    @mock.patch('poolnfc.poolbot._get_poolbot_users')
    @mock.patch('poolnfc.nfc.raw_input')
    @mock.patch.object(nfc.Game, 'read_uid')
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

        game = nfc.Game()
        game.new_users_loop(infinite=False)

        db = shelve.open(test_config.DB_FILE_PATH)
        self.assertEqual(len(db['lukasz']['uids']), 1)
        db.close()

    @mock.patch('poolnfc.poolbot.config', test_config)
    @mock.patch('poolnfc.poolbot._get_poolbot_users')
    @mock.patch('poolnfc.nfc.raw_input')
    @mock.patch.object(nfc.Game, 'read_uid')
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

        game = nfc.Game()
        game.new_users_loop(infinite=False)

        db = shelve.open(test_config.DB_FILE_PATH)
        self.assertEqual(len(db['lukasz']['uids']), 1)
        db.close()