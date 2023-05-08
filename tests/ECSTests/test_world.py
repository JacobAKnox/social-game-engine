import logging
import unittest
import uuid

import ECS
import Events
import Storage
from ECS import World, int_to_uuid, unpack_components
from tests.ECSTests import TestComponent, TestComponent2, UnusedTestComponent
from tests.StorageTests.test_storage import TEST_DATABASE_NAME, TEST_ENTITY_COLLECTION

logging.disable(logging.CRITICAL)


async def test_processor(world: World, *args, **kwargs):
    return 1


class WorldTestCase(unittest.IsolatedAsyncioTestCase):

    @classmethod
    def setUpClass(cls):
        ECS.add_component_mapping(TestComponent, TestComponent2)
        Storage.configure_database(TEST_DATABASE_NAME, TEST_ENTITY_COLLECTION)

    def setUp(self):
        self.world = World()
        self.entity1_components = (TestComponent(5, "2"),)
        self.entity2_components = (TestComponent2(), TestComponent())
        self.processor = test_processor
        Events.EVENT_MANAGER.clear()

    def tearDown(self) -> None:
        self.world._entities = {}
        Events.EVENT_MANAGER.clear()

    def test_world_entity(self):
        temp_uuid = uuid.uuid4()
        self.assertIsNone(self.world.remove_entity(temp_uuid))
        self.assertFalse(self.world.has_entity(temp_uuid))

        temp_uuid = self.world.add_components(None, *self.entity1_components)
        self.assertTrue(self.world.has_entity(temp_uuid))
        self.assertEqual(self.world.get_components(temp_uuid), {type(c): c for c in self.entity1_components})
        self.assertEqual(tuple(self.world.remove_entity(temp_uuid).values()), self.entity1_components)
        self.assertFalse(self.world.has_entity(temp_uuid))

        self.world.add_components(temp_uuid, TestComponent())
        self.world.add_components(temp_uuid)
        self.assertTrue(TestComponent in self.world.get_components(temp_uuid))

        self.world.remove_entity(temp_uuid)

        self.world.add_components(temp_uuid, TestComponent())
        self.world.add_components(temp_uuid, TestComponent2())
        self.assertTrue(TestComponent2 in self.world.get_components(temp_uuid))
        self.assertTrue(TestComponent in self.world.get_components(temp_uuid))

    async def test_world_processor(self):
        assert await self.world.run_processor(self.processor) == 1

    def test_component_cache(self):
        self.assertEqual(self.world._components_cache, {})

        self.world.remove_from_component_cache(uuid.uuid4(), TestComponent)
        self.assertEqual(self.world._components_cache, {})

        temp_uuid = uuid.uuid4()
        temp_uuid2 = uuid.uuid4()

        self.world.add_to_component_cache(temp_uuid, TestComponent)
        self.assertEqual(self.world._components_cache, {TestComponent: {temp_uuid}})

        self.world.add_to_component_cache(temp_uuid, TestComponent)
        self.assertEqual(self.world._components_cache, {TestComponent: {temp_uuid}})

        self.world.add_to_component_cache(temp_uuid2, TestComponent2)
        self.assertEqual(self.world._components_cache, {TestComponent: {temp_uuid},
                                                        TestComponent2: {temp_uuid2}})

        self.world.add_to_component_cache(temp_uuid2, TestComponent)
        self.assertEqual(self.world._components_cache, {TestComponent: {temp_uuid,
                                                                        temp_uuid2},
                                                        TestComponent2: {temp_uuid2}})

        self.world.remove_from_component_cache(temp_uuid2, TestComponent)
        self.assertEqual(self.world._components_cache, {TestComponent: {temp_uuid},
                                                        TestComponent2: {temp_uuid2}})

        self.world.remove_from_component_cache(temp_uuid, TestComponent)
        self.assertEqual(self.world._components_cache, {TestComponent: set(),
                                                        TestComponent2: {temp_uuid2}})

        self.world.remove_from_component_cache(temp_uuid, TestComponent2)
        self.assertEqual(self.world._components_cache, {TestComponent: set(),
                                                        TestComponent2: {temp_uuid2}})

    def test_query(self):
        temp_uuid = self.world.add_components(None, *self.entity1_components)
        temp_uuid2 = self.world.add_components(None, *self.entity2_components)

        self.assertEqual(self.world.query_components(UnusedTestComponent), set())

        self.assertEqual(self.world.query_components(TestComponent), {temp_uuid, temp_uuid2})

        self.assertEqual(self.world.query_components(TestComponent2), {temp_uuid2})

        self.assertEqual(self.world.query_components(TestComponent, TestComponent2), {temp_uuid2})

        self.assertEqual(self.world.query_components(TestComponent, TestComponent2, UnusedTestComponent), set())

    async def test_auto_register_event_single(self):
        self.world.register_processor_events(test_processor, "foo")
        self.assertEqual(await Events.EVENT_MANAGER.dispatch_event("foo"), [1])

        self.world.register_processor_events(test_processor, "bar")
        self.assertEqual(await Events.EVENT_MANAGER.dispatch_event("bar"), [1])

        self.world.unregister_processor_events(test_processor)
        self.assertEqual(await Events.EVENT_MANAGER.dispatch_event("foo"), [])
        Events.EVENT_MANAGER.clear()

        self.world.unregister_processor_events(test_processor)

    async def test_auto_register_event_multiple(self):
        self.world.register_processor_events(test_processor, "foo", "bar")
        self.assertEqual(await Events.EVENT_MANAGER.dispatch_event("foo"), [1])
        self.assertEqual(await Events.EVENT_MANAGER.dispatch_event("bar"), [1])

        self.world.unregister_processor_events(test_processor)
        self.assertEqual(await Events.EVENT_MANAGER.dispatch_event("foo"), [])
        self.assertEqual(await Events.EVENT_MANAGER.dispatch_event("bar"), [])
        Events.EVENT_MANAGER.clear()

    async def test_int_to_uuid(self):
        self.assertNotEqual(int_to_uuid(0), uuid.UUID(int=0, version=4))

        uuid_ = uuid.uuid4()
        self.assertEqual(uuid_, int_to_uuid(uuid_.int))

    async def test_unpack_components(self):
        data = {TestComponent: TestComponent(), TestComponent2: TestComponent2()}
        self.assertEqual(unpack_components(data[TestComponent], data[TestComponent2]), data)

        self.assertEqual(unpack_components(data[TestComponent], data[TestComponent2], TestComponent()), data)

    async def test_get_components(self):
        self.assertIsNone(self.world.get_components(uuid.uuid4()))

        data = {TestComponent: TestComponent(), TestComponent2: TestComponent2()}
        temp_uuid = self.world.add_components(None, data[TestComponent], data[TestComponent2])

        self.assertEqual(self.world.get_components(temp_uuid), data)

        self.assertEqual(self.world.get_components(temp_uuid, TestComponent), {TestComponent: data[TestComponent]})

        self.assertEqual(self.world.get_components(temp_uuid, TestComponent, TestComponent2), data)

    async def test_compare_entities(self):
        id1 = self.world.add_components(None, *self.entity2_components)
        id2 = self.world.add_components(None, *self.entity1_components)

        self.assertFalse(ECS.compare_entities(self.world, id1, id2))  # test fail on different components

        id2 = self.world.add_components(None, TestComponent(txt="other value"), TestComponent2())

        self.assertFalse(ECS.compare_entities(self.world, id1, id2))  # test fail with same components but not equal

        id2 = self.world.add_components(None, *self.entity2_components)

        self.assertTrue(ECS.compare_entities(self.world, id1, id2))  # test success

    async def test_entity_from_dict(self):
        self.assertIsNone(ECS.entity_from_dict({}))

        id1 = self.world.add_components(None, *self.entity2_components)
        data = self.world.get_entity_data(id1)

        copy = ECS.entity_from_dict(data)
        self.assertEqual(copy[0], id1)

        id2 = self.world.add_components(None, *(copy[1]))

        self.assertTrue(ECS.compare_entities(self.world, id1, id2))

    async def test_get_entity_data(self):
        self.assertIsNone(self.world.get_entity_data(uuid.uuid4()))

        id1 = self.world.add_components(None, *self.entity2_components)

        data = ECS.entity_from_dict(self.world.get_entity_data(id1))
        id2 = self.world.add_components(None, *(data[1]))

        self.assertEqual(data[0], id1)
        self.assertTrue(ECS.compare_entities(self.world, id1, id2))

    async def test_save_entity(self):
        id1 = self.world.add_components(None, *self.entity1_components)
        id2 = uuid.uuid4()

        self.world.save_entity(id2)
        self.assertIsNone(Storage.load_entity(id2))

        self.world.save_entity(id1)
        self.assertIsNotNone(Storage.load_entity(id1))

    async def test_add_entities(self):
        id1 = self.world.add_components(None, *self.entity1_components)
        id2 = self.world.add_components(None, *self.entity1_components)
        id3 = self.world.add_components(None, *self.entity1_components)

        self.world.save_entity(id1)
        self.world.save_entity(id2)
        self.world.save_entity(id3)

        self.world._entities = {}

        self.world.add_entities(*Storage.load_all_entities(), {})

        self.assertTrue(self.world.has_entity(id1))
        self.assertTrue(self.world.has_entity(id2))
        self.assertTrue(self.world.has_entity(id3))

    async def test_remove_components(self):
        id = self.world.add_components(None, *self.entity1_components)

        self.assertEqual(self.world.remove_components(id, TestComponent2), None)
        self.assertEqual(self.world.get_components(id), {type(c): c for c in self.entity1_components})

        id = self.world.add_components(None, *self.entity1_components)

        temp_id = self.world.add_components(None, *self.entity2_components)

        self.assertEqual(self.world.remove_components(id, TestComponent2), None)
        self.assertEqual(self.world.get_components(id), {type(c): c for c in self.entity1_components})

        id = self.world.add_components(None, *self.entity2_components)

        self.assertEqual(self.world.remove_components(id, TestComponent), {TestComponent: TestComponent()})
        self.assertEqual(self.world.get_components(id), {TestComponent2: TestComponent2()})

        id = self.world.add_components(None, *self.entity2_components)

        self.assertEqual(self.world.remove_components(id, TestComponent, TestComponent2),
                         {type(c): c for c in self.entity2_components})
        self.assertEqual(self.world.get_components(id), {})

        id = uuid.uuid4()
        self.assertEqual(self.world.remove_components(id, TestComponent, TestComponent2), None)
