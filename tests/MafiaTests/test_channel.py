import logging
import unittest
from unittest.mock import AsyncMock

import ECS
import Storage
import UI
from Mafia import Guild, Channel, register_channel, send_message
from tests.StorageTests.test_storage import TEST_DATABASE_NAME, TEST_ENTITY_COLLECTION

logging.disable(logging.CRITICAL)


class ChannelTestCase(unittest.IsolatedAsyncioTestCase):

    @classmethod
    def setUpClass(cls):
        ECS.add_component_mapping(Channel, Guild)
        Storage.configure_database(TEST_DATABASE_NAME, TEST_ENTITY_COLLECTION)

    def setUp(self) -> None:
        self.world = ECS.World()

    def tearDown(self) -> None:
        Storage.clear_entity_collection()

    async def test_register_channel(self):
        self.assertEqual(len(self.world.query_components(Channel)), 0)

        await self.world.run_processor(register_channel, channel_id=123)

        query = list(self.world.query_components(Channel))

        self.assertEqual(len(query), 1)

        components = self.world.get_components(query[0])
        self.assertEqual(len(components), 1)
        self.assertEqual(components[Channel], Channel(123))

    async def test_send_message(self):
        UI.send_message = AsyncMock()

        self.world.add_components(None, Channel(123))

        await self.world.run_processor(send_message, message="test")

        UI.send_message.assert_called_once_with("test", 123)
