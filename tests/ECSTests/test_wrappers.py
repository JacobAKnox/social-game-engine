import logging
import unittest
import uuid

import ECS
from ECS import World
from ECS.ECSWrappers import _check_world_argument, query, InvalidParameterError, _extract_world, query_component_loop, \
    query_entity_loop, StopProcess, query_entity_component_loop
from tests.ECSTests import TestComponent, TestComponent2

logging.disable(logging.CRITICAL)


class WrapperTestCase(unittest.IsolatedAsyncioTestCase):

    @classmethod
    def setUpClass(cls) -> None:
        ECS.add_component_mapping(TestComponent)

    def setUp(self) -> None:
        pass

    def test_check_world_argument(self):
        def func_without_world():
            pass

        def func_with_world_no_annotation(world):
            pass

        def func_with_world_wrong_annotation(world: int):
            pass

        def func_with_world_and_annotations(world: World, test):
            pass

        self.assertFalse(_check_world_argument(func_without_world))

        self.assertFalse(_check_world_argument(func_with_world_no_annotation))

        self.assertFalse(_check_world_argument(func_with_world_wrong_annotation))

        self.assertTrue(_check_world_argument(func_with_world_and_annotations))

    def test_extract_world(self):
        world = World()
        world2 = World()

        self.assertRaises(KeyError, _extract_world)

        self.assertRaises(KeyError, _extract_world, key=123)

        self.assertRaises(KeyError, _extract_world, world=123, key=world)

        self.assertRaises(KeyError, _extract_world, world=123, key=world)

        self.assertEqual(_extract_world(world=world, key=123), world)

        self.assertRaises(KeyError, _extract_world, 123, 2, 4)

        self.assertEqual(_extract_world(123, world), world)

        self.assertEqual(_extract_world(world2, world=world), world)

    async def test_query_wrapper(self):
        world_ = World()

        try:
            @query("test", TestComponent)
            async def func_without_world():
                pass

            assert False
        except InvalidParameterError:
            assert True

        @query("test", TestComponent)
        async def func_with_world(world: World, **kwargs):
            return len(kwargs["test"])

        self.assertEqual(await world_.run_processor(func_with_world), 0)

        id1 = world_.add_components(None, TestComponent())

        self.assertEqual(await world_.run_processor(func_with_world), 1)

        id2 = world_.add_components(None, TestComponent())

        self.assertEqual(await world_.run_processor(func_with_world), 2)

        world_.remove_entity(id1)
        world_.remove_entity(id2)

        self.assertEqual(await world_.run_processor(func_with_world), 0)

    async def test_query_component_loop_wrapper(self):
        world_ = World()

        try:
            @query_component_loop("test", None, TestComponent)
            async def func_without_world():
                pass

            assert False
        except InvalidParameterError:
            assert True

        @query_component_loop("test", None, TestComponent, TestComponent2)
        async def test_without_aggregator(world: World, *args, **kwargs):
            components = kwargs["test"]
            if TestComponent not in components or TestComponent2 not in components:
                assert False
            test_without_aggregator.counter += 1

        @query_component_loop("test", sum, TestComponent, TestComponent2)
        async def test_with_aggregator(world: World, *args, **kwargs):
            components = kwargs["test"]
            if TestComponent not in components or TestComponent2 not in components:
                assert False
            test_with_aggregator.counter += 1
            return 1

        test_without_aggregator.counter = 0
        test_with_aggregator.counter = 0

        world_.add_components(None, TestComponent())
        world_.add_components(None, TestComponent2())
        world_.add_components(None, TestComponent(), TestComponent2())
        world_.add_components(None, TestComponent(), TestComponent2())
        world_.add_components(None, TestComponent(), TestComponent2())

        self.assertIsNone(await world_.run_processor(test_without_aggregator))
        self.assertEqual(test_without_aggregator.counter, 3)

        self.assertEqual(await world_.run_processor(test_with_aggregator), 3)
        self.assertEqual(test_with_aggregator.counter, 3)

    async def test_query_entity_loop_wrapper(self):
        world_ = World()

        try:
            @query_entity_loop("test", None, TestComponent)
            async def func_without_world():
                pass

            assert False
        except InvalidParameterError:
            assert True

        @query_entity_loop("test", None, TestComponent, TestComponent2)
        async def test_without_aggregator(world: World, *args, **kwargs):
            components = world.get_components(kwargs["test"])
            if TestComponent not in components or TestComponent2 not in components:
                assert False
            test_without_aggregator.counter += 1

        @query_entity_loop("test", sum, TestComponent, TestComponent2)
        async def test_with_aggregator(world: World, *args, **kwargs):
            components = world.get_components(kwargs["test"])
            if TestComponent not in components or TestComponent2 not in components:
                assert False
            test_with_aggregator.counter += 1
            return 1

        test_without_aggregator.counter = 0
        test_with_aggregator.counter = 0

        world_.add_components(None, TestComponent())
        world_.add_components(None, TestComponent2())
        world_.add_components(None, TestComponent(), TestComponent2())
        world_.add_components(None, TestComponent(), TestComponent2())
        world_.add_components(None, TestComponent(), TestComponent2())

        self.assertIsNone(await world_.run_processor(test_without_aggregator))
        self.assertEqual(test_without_aggregator.counter, 3)

        self.assertEqual(await world_.run_processor(test_with_aggregator), 3)
        self.assertEqual(test_with_aggregator.counter, 3)

    async def test_query_entity_component_loop_wrapper(self):
        world_ = World()

        try:
            @query_entity_component_loop("test", None, TestComponent)
            async def func_without_world():
                pass

            assert False
        except InvalidParameterError:
            assert True

        @query_entity_component_loop("test", None, TestComponent, TestComponent2)
        async def test_without_aggregator(world: World, *args, **kwargs):
            data = kwargs["test"]
            components = data[1]
            id = data[0]
            if not isinstance(id, uuid.UUID):
                assert False
            if TestComponent not in components or TestComponent2 not in components:
                assert False
            test_without_aggregator.counter += 1

        @query_entity_component_loop("test", sum, TestComponent, TestComponent2)
        async def test_with_aggregator(world: World, *args, **kwargs):
            data = kwargs["test"]
            components = data[1]
            id = data[0]
            if not isinstance(id, uuid.UUID):
                assert False
            if TestComponent not in components or TestComponent2 not in components:
                assert False
            test_with_aggregator.counter += 1
            return 1

        test_without_aggregator.counter = 0
        test_with_aggregator.counter = 0

        id1 = world_.add_components(None, TestComponent())
        id2 = world_.add_components(None, TestComponent2())
        id3 = world_.add_components(None, TestComponent(), TestComponent2())
        id4 = world_.add_components(None, TestComponent(), TestComponent2())
        id5 = world_.add_components(None, TestComponent(), TestComponent2())

        self.assertIsNone(await world_.run_processor(test_without_aggregator))
        self.assertEqual(test_without_aggregator.counter, 3)

        self.assertEqual(await world_.run_processor(test_with_aggregator), 3)
        self.assertEqual(test_with_aggregator.counter, 3)

    async def test_stop_iteration(self):
        world_ = World()

        for i in range(10):
            world_.add_components(None, TestComponent(num=1))

        @query_component_loop("test", None, TestComponent)
        async def stop_component_loop(world: World, *args, **kwargs):
            stop_component_loop.counter += 1
            if stop_component_loop.counter == 4:
                raise StopProcess

        stop_component_loop.counter = 0

        @query_entity_loop("test", None, TestComponent)
        async def stop_entity_loop(world: World, *args, **kwargs):
            stop_entity_loop.counter += 1
            if stop_entity_loop.counter == 4:
                raise StopProcess

        stop_entity_loop.counter = 0

        @query_entity_component_loop("test", None, TestComponent)
        async def stop_entity_component_loop(world: World, *args, **kwargs):
            stop_entity_component_loop.counter += 1
            if stop_entity_component_loop.counter == 4:
                raise StopProcess

        stop_entity_component_loop.counter = 0

        await world_.run_processor(stop_component_loop)
        await world_.run_processor(stop_entity_loop)

        self.assertEqual(stop_component_loop.counter, 4)
        self.assertEqual(stop_entity_loop.counter, 4)

    async def test_stop_return(self):
        world_ = World()

        for i in range(10):
            world_.add_components(None, TestComponent(num=1))

        @query_component_loop("test", sum, TestComponent)
        async def test_stop_return(world: World, *args, **kwargs):
            test_stop_return.counter += kwargs["test"][TestComponent].test_int
            if test_stop_return.counter == 4:
                raise StopProcess(1)
            return 1

        test_stop_return.counter = 0

        self.assertEqual(await world_.run_processor(test_stop_return), 4)

        self.assertEqual(test_stop_return.counter, 4)
