import logging
import unittest

import ECS
from ECS.UtilityComponents import IntWrapper
from Mafia import Channel

logging.disable(logging.CRITICAL)


class IntWrapperTest(IntWrapper):
    @classmethod
    def data_key(cls) -> str:
        return "test"


class IntWrapperTestCase(unittest.IsolatedAsyncioTestCase):

    @classmethod
    def setUpClass(cls):
        ECS.add_component_mapping(IntWrapperTest)

    def test_int_wrapper(self):
        int_test = IntWrapperTest(123)
        self.assertEqual(int_test.data, 123)

        data = int_test.__dict__()
        self.assertEqual(int_test.data, data[int_test.data_key()])

        int_test2 = IntWrapperTest.from_dict(data)
        self.assertEqual(int_test.data, int_test2.data)

        int_test3 = IntWrapperTest(456)
        self.assertNotEqual(int_test, int_test3)

        channel = Channel(123)
        self.assertNotEqual(int_test, channel)

        self.assertEqual(int_test, int_test2)
