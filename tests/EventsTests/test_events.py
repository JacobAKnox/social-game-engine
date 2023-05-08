import logging
import unittest

import Events
from ECS import World

logging.disable(logging.CRITICAL)


async def safe_handler_no_args(*args):
    return True


async def handler_no_args():
    return True


async def handler_one_arg(arg, *args):
    return arg


async def handler_two_args(arg1, arg2, *args):
    return arg2 + arg1


async def handler_throws():
    raise Exception("test_events exception message")


class EventsTestCase(unittest.IsolatedAsyncioTestCase):

    def tearDown(self) -> None:
        Events.EVENT_MANAGER.clear()

    async def test_handler_management(self):
        Events.EVENT_MANAGER.remove_handler("foo", safe_handler_no_args)
        self.assertEqual(await Events.EVENT_MANAGER.dispatch_event("foo"), [])

        Events.EVENT_MANAGER.set_handler("foo", safe_handler_no_args)
        self.assertEqual(await Events.EVENT_MANAGER.dispatch_event("foo"), [True])

        Events.EVENT_MANAGER.set_handler("foo", handler_one_arg)
        self.assertEqual(await Events.EVENT_MANAGER.dispatch_event("foo", 1), [1, True])

        Events.EVENT_MANAGER.remove_handler("foo", safe_handler_no_args)
        self.assertEqual(await Events.EVENT_MANAGER.dispatch_event("foo", 1), [1])

        Events.EVENT_MANAGER.remove_handler("foo", handler_one_arg)
        self.assertEqual(await Events.EVENT_MANAGER.dispatch_event("foo", 1), [])

    async def test_event_dispatch_no_handlers(self):
        self.assertEqual(await Events.EVENT_MANAGER.dispatch_event("foo"), [])
        self.assertEqual(await Events.EVENT_MANAGER.dispatch_event("foo", 1), [])
        self.assertEqual(await Events.EVENT_MANAGER.dispatch_event("foo", 1, 2), [])

    async def test_event_dispatch_one_arg(self):
        Events.EVENT_MANAGER.set_handler("foo", handler_one_arg)
        self.assertEqual(await Events.EVENT_MANAGER.dispatch_event("foo", 1), [1])

    async def test_event_dispatch_two_args(self):
        Events.EVENT_MANAGER.set_handler("foo", handler_two_args)
        self.assertEqual(await Events.EVENT_MANAGER.dispatch_event("foo", 1, 2), [3])

    async def test_event_dispatch_no_args(self):
        Events.EVENT_MANAGER.set_handler("foo", safe_handler_no_args)
        self.assertEqual(await Events.EVENT_MANAGER.dispatch_event("foo"), [True])

    async def test_event_dispatch_incorrect_args(self):
        Events.EVENT_MANAGER.set_handler("foo", handler_no_args)
        # makes sure function raises a type error
        try:
            await Events.EVENT_MANAGER.dispatch_event("foo", 1)
            assert False
        except TypeError:
            assert True

    async def test_exception_handling(self):
        Events.EVENT_MANAGER.set_handler("foo", handler_throws)

        try:
            results = await Events.EVENT_MANAGER.dispatch_event("foo")
            for result in results:
                if isinstance(result, Exception):
                    assert False
        except Exception:
            assert False
        assert True

    async def test_set_instance_method_as_handler(self):
        class MyClass:
            value = 0

            async def process(self, world: World, *args, **kwargs):
                return self.value

        my_class = MyClass()
        Events.EVENT_MANAGER.set_handler("foo", my_class.process)
        self.assertEqual(await Events.EVENT_MANAGER.dispatch_event("foo", World()), [0])
