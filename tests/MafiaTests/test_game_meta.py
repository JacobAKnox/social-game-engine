import logging
import unittest
import uuid
from asyncio import sleep
from unittest.mock import AsyncMock

import ECS
import Events
import Mafia
import Storage
import UI
from Events import EventList
from Mafia import Channel, GameMeta, Guild
from tests.StorageTests.test_storage import TEST_DATABASE_NAME, TEST_ENTITY_COLLECTION

logging.disable(logging.CRITICAL)


class ChannelTestCase(unittest.IsolatedAsyncioTestCase):

    @classmethod
    def setUpClass(cls):
        ECS.add_component_mapping(GameMeta, Guild)
        Storage.configure_database(TEST_DATABASE_NAME, TEST_ENTITY_COLLECTION)

    def tearDown(self) -> None:
        Storage.clear_entity_collection()

    def test_game_meta(self):
        game_meta = GameMeta()
        self.assertIsNotNone(game_meta.uuid)

        uuid_ = uuid.uuid4()
        game_meta = GameMeta(int(uuid_))
        self.assertEqual(game_meta.uuid, uuid_)

        data = game_meta.__dict__()
        self.assertEqual(game_meta.uuid, data["id"])

        game_meta2 = GameMeta.from_dict(data)
        self.assertEqual(game_meta.uuid, game_meta2.uuid)

        game_meta3 = GameMeta(int(uuid.uuid4()))
        self.assertNotEqual(game_meta, game_meta3)

        channel = Channel(123)
        self.assertNotEqual(game_meta, channel)

        self.assertEqual(game_meta, game_meta2)

    async def test_create_game(self):
        world = ECS.World()

        Events.EVENT_MANAGER.dispatch_event = AsyncMock()

        self.assertTrue(await Mafia.create_game(world, guild=123))
        self.assertEqual(len(world.query_components(GameMeta, Guild)), 1)
        uuid_ = list(world.query_components(GameMeta, Guild))[0]
        self.assertIsNotNone(Storage.load_entity(uuid_))

        Events.EVENT_MANAGER.dispatch_event.assert_called_with(EventList.PRE_CREATE_GAME_EVENT, uuid=uuid_)

        self.assertFalse(await Mafia.create_game(world, guild=123))

    async def test_remove_games(self):
        world = ECS.World()

        UI.make_role = AsyncMock(return_value=678)
        Events.EVENT_MANAGER.dispatch_event = AsyncMock()

        self.assertEqual(await Mafia.remove_games(world), 0)
        await sleep(0.05)
        self.assertEqual(len(world.query_components(GameMeta)), 0)
        self.assertEqual(len(Storage.load_all_entities()), 0)

        await Mafia.create_game(world, guild=123)

        entity_id = list(world.query_components(GameMeta))[0]

        self.assertEqual(await Mafia.remove_games(world), 1)
        await sleep(0.05)
        self.assertEqual(len(world.query_components(GameMeta)), 0)
        self.assertEqual(len(Storage.load_all_entities()), 0)

        Events.EVENT_MANAGER.dispatch_event.assert_called_with(EventList.PRE_REMOVE_GAME_EVENT, uuid=entity_id)

        await Mafia.create_game(world, guild=123)
        await Mafia.create_game(world, guild=456)

        self.assertEqual(await Mafia.remove_games(world), 1)
        await sleep(0.05)
        self.assertEqual(len(world.query_components(GameMeta)), 0)
        self.assertEqual(len(Storage.load_all_entities()), 0)

    async def test_remove_game(self):
        world = ECS.World()

        UI.make_role = AsyncMock(return_value=678)
        Events.EVENT_MANAGER.dispatch_event = AsyncMock()

        self.assertFalse(await Mafia.remove_game(world, guild=123))
        await sleep(0.05)
        self.assertEqual(len(world.query_components(GameMeta, Guild)), 0)
        self.assertEqual(len(Storage.load_all_entities()), 0)

        await Mafia.create_game(world, guild=123)

        entity_id = list(world.query_components(GameMeta))[0]

        self.assertEqual(len(world.query_components(GameMeta, Guild)), 1)
        self.assertEqual(len(Storage.load_all_entities()), 1)

        self.assertFalse(await Mafia.remove_game(world, guild=456))
        await sleep(0.05)
        self.assertEqual(len(world.query_components(GameMeta, Guild)), 1)
        self.assertEqual(len(Storage.load_all_entities()), 1)

        self.assertTrue(await Mafia.remove_game(world, guild=123))
        await sleep(0.05)
        self.assertEqual(len(world.query_components(GameMeta, Guild)), 0)
        self.assertEqual(len(Storage.load_all_entities()), 0)

        Events.EVENT_MANAGER.dispatch_event.assert_called_with(EventList.PRE_REMOVE_GAME_EVENT, uuid=entity_id)

    async def test_game_exists(self):
        world = ECS.World()

        self.assertFalse(await Mafia.game_exists(world, guild=123))

        await Mafia.create_game(world, guild=123)

        self.assertTrue(await Mafia.game_exists(world, guild=123))

        self.assertFalse(await Mafia.game_exists(world, guild=456))
