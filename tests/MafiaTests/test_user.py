import logging
import unittest
from unittest.mock import AsyncMock

import ECS
import Storage
import UI
from ECS import World
from Mafia import DiscordUser, GameMeta, Guild
from Mafia.Channel import PlayerChannel, PlayerCommandChannel, PlayerCategory, PlayerRole, GameNotRunningException
from Mafia.User import register_user, unregister_user, make_channels, check_user_exists, remove_user_channels, \
    add_player_role, remove_player_role
from tests.ECSTests import TestComponent
from tests.StorageTests.test_storage import TEST_DATABASE_NAME, TEST_ENTITY_COLLECTION

logging.disable(logging.CRITICAL)


class UserTestCase(unittest.IsolatedAsyncioTestCase):

    @classmethod
    def setUpClass(cls):
        ECS.add_component_mapping(DiscordUser)
        Storage.configure_database(TEST_DATABASE_NAME, TEST_ENTITY_COLLECTION)

    def tearDown(self) -> None:
        Storage.clear_entity_collection()

    def test_discord_user(self):
        user = DiscordUser(user_id=123, display_name="test")
        self.assertEqual(user.discord_id, 123)
        self.assertEqual(user.display_name, "test")

        data = user.__dict__()
        self.assertEqual(user.discord_id, data["discord_id"])
        self.assertEqual(user.display_name, data["display_name"])

        user2 = DiscordUser.from_dict(data)
        self.assertEqual(user.discord_id, user2.discord_id)
        self.assertEqual(user.display_name, user2.display_name)

        self.assertEqual(user, user2)
        user2.display_name = "foo"
        self.assertEqual(user, user2)  # test that equality doesn't depend on name
        user2.discord_id = 456
        self.assertNotEqual(user, user2)  # test that equality is based on discord id

        self.assertNotEqual(user, TestComponent())

    async def test_register_user(self):
        world = World()

        await register_user(world, discord_id=1234, display_name="test")

        query = list(world.query_components(DiscordUser))
        self.assertEqual(len(query), 1)
        self.assertEqual(world.get_components(query[0])[DiscordUser], DiscordUser(user_id=1234, display_name="test"))

        self.assertEqual(len(world.get_components(query[0])), 1)

        component: DiscordUser = world.get_components(query[0], DiscordUser)[DiscordUser]
        self.assertEqual(component.discord_id, 1234)
        self.assertEqual(component.display_name, "test")

    async def test_unregister_user(self):
        world = World()

        self.assertFalse(await world.run_processor(unregister_user, discord_id=123))

        await register_user(world, discord_id=1, display_name="test")
        await register_user(world, discord_id=2, display_name="test")
        await register_user(world, discord_id=3, display_name="test")

        self.assertTrue(await world.run_processor(unregister_user, discord_id=2))

        query = list(world.query_components(DiscordUser))
        self.assertEqual(len(query), 2)

        for user in query:
            discord_user: DiscordUser = world.get_components(user, DiscordUser)[DiscordUser]
            assert discord_user.discord_id != 2

    async def test_make_channels(self):
        world = World()

        game_id = world.add_components(None, GameMeta(), Guild(123))
        user_id = world.add_components(None, DiscordUser(456, "test"))
        UI.make_player_channels = AsyncMock(return_value=(789, 321, 654))

        await world.run_processor(make_channels, entity_id=user_id)

        entity = world.get_components(user_id)
        self.assertTrue(PlayerChannel in entity)
        self.assertTrue(PlayerCommandChannel in entity)
        self.assertTrue(PlayerCategory in entity)

        self.assertEqual(entity[PlayerChannel].data, 789)
        self.assertEqual(entity[PlayerCommandChannel].data, 321)
        self.assertEqual(entity[PlayerCategory].data, 654)

    async def test_remove_channels(self):
        world = World()
        UI.remove_channels = AsyncMock()

        game_id = world.add_components(None, GameMeta(), Guild(123))

        user_id = world.add_components(None, DiscordUser(456, "test"))
        await world.run_processor(remove_user_channels, entity_id=user_id)
        UI.remove_channels.assert_called_with(123)

        user_id = world.add_components(None, DiscordUser(456, "test"), PlayerChannel(789))
        await world.run_processor(remove_user_channels, entity_id=user_id)
        UI.remove_channels.assert_called_with(123, 789)

        user_id = world.add_components(None, DiscordUser(456, "test"), PlayerChannel(789), PlayerCommandChannel(321))
        await world.run_processor(remove_user_channels, entity_id=user_id)
        UI.remove_channels.assert_called_with(123, 789, 321)

        user_id = world.add_components(None, DiscordUser(456, "test"), PlayerChannel(789), PlayerCommandChannel(321),
                                       PlayerCategory(654))
        await world.run_processor(remove_user_channels, entity_id=user_id)
        UI.remove_channels.assert_called_with(123, 654, 789, 321)

    async def test_check_user_exists(self):
        world = World()

        self.assertFalse(await world.run_processor(check_user_exists, user=123))

        world.add_components(None, DiscordUser(123, ""))
        self.assertTrue(await world.run_processor(check_user_exists, user=123))

        world.add_components(None, DiscordUser(456, ""))
        world.add_components(None, DiscordUser(789, ""))
        self.assertTrue(await world.run_processor(check_user_exists, user=123))
        self.assertTrue(await world.run_processor(check_user_exists, user=456))
        self.assertTrue(await world.run_processor(check_user_exists, user=789))

    async def test_add_role(self):
        world = World()

        UI.assign_role = AsyncMock()

        id_ = world.add_components(None, DiscordUser(789, "test"))

        with self.assertRaises(GameNotRunningException):
            await world.run_processor(add_player_role, entity_id=id_)
        UI.assign_role.assert_not_called()

        world.add_components(None, Guild(123), GameMeta(), PlayerRole(456))

        await world.run_processor(add_player_role, entity_id=id_)
        UI.assign_role.assert_called_with(789, 123, 456)

    async def test_remove_role(self):
        world = World()

        UI.remove_role = AsyncMock()

        id_ = world.add_components(None, DiscordUser(789, "test"))

        with self.assertRaises(GameNotRunningException):
            await world.run_processor(remove_player_role, entity_id=id_)
        UI.remove_role.assert_not_called()

        world.add_components(None, Guild(123), GameMeta(), PlayerRole(456))

        await world.run_processor(remove_player_role, entity_id=id_)
        UI.remove_role.assert_called_with(789, 123, 456)
