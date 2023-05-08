import logging
import unittest

from Events.EventWrappers import check_argument

logging.disable(logging.CRITICAL)


class WrapperTestCase(unittest.IsolatedAsyncioTestCase):

    def test_check_argument_wrapper(self):
        @check_argument("TestArg", int)
        def test_func(**kwargs):
            return kwargs["TestArg"] == 5

        @check_argument("TestArg")
        def test_func2(**kwargs):
            return "TestArg" in kwargs

        self.assertRaises(ValueError, test_func)

        self.assertRaises(ValueError, test_func, TestArg="test")

        self.assertFalse(test_func(TestArg=3))
        self.assertTrue(test_func(TestArg=5))

        self.assertRaises(ValueError, test_func2)

        self.assertTrue(test_func2(TestArg="test"))
        self.assertTrue(test_func2(TestArg=5))
