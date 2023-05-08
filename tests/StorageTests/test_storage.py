import logging
import unittest
import uuid

import ECS
import Storage
from ECS import World
from Storage import configure_database
from tests import ECSTests
from tests.ECSTests import TestComponent

TEST_DATABASE_NAME = "MafiaUnitTest"
TEST_ENTITY_COLLECTION = "Entities"

logging.disable(logging.CRITICAL)


class StorageTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        ECSTests.register_test_components()
        configure_database(TEST_DATABASE_NAME, TEST_ENTITY_COLLECTION)

    def setUp(self):
        self.world = World()
        self.test_entity_id: uuid = self.world.add_components(None, TestComponent(num=5))

    def tearDown(self) -> None:
        pass  # left to make commenting bottom part easier when debugging
        Storage.clear_entity_collection()

    def test_save_entity(self):
        self.assertRaises(KeyError, Storage.save_entity, {})

        Storage.save_entity(self.world.get_entity_data(self.test_entity_id))
        loaded = ECS.entity_from_dict(Storage.load_entity(self.test_entity_id))
        self.assertEqual(loaded[0], self.test_entity_id)
        id2 = self.world.add_components(None, *(loaded[1]))
        ECS.compare_entities(self.world, self.test_entity_id, id2)

    def test_delete_entity(self):
        Storage.save_entity(self.world.get_entity_data(self.test_entity_id))
        self.assertIsNotNone(Storage.load_entity(self.test_entity_id))

        Storage.remove_entity(self.test_entity_id)

        self.assertIsNone(Storage.load_entity(self.test_entity_id))

    def test_load_entity(self):
        Storage.save_entity(self.world.get_entity_data(self.test_entity_id))
        loaded = ECS.entity_from_dict(Storage.load_entity(self.test_entity_id))
        self.assertEqual(loaded[0], self.test_entity_id)
        id2 = self.world.add_components(None, *(loaded[1]))
        ECS.compare_entities(self.world, self.test_entity_id, id2)

        self.assertIsNone(Storage.load_entity(uuid.uuid4()))

    def test_load_entities(self):
        id1 = self.world.add_components(None)
        id2 = self.world.add_components(None)

        Storage.save_entity(self.world.get_entity_data(self.test_entity_id))
        Storage.save_entity(self.world.get_entity_data(id1))
        Storage.save_entity(self.world.get_entity_data(id2))

        retrieved = Storage.load_all_entities()

        self.assertEqual(len(retrieved), 3)
