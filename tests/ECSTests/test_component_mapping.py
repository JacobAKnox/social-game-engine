import logging
import unittest

import ECS
from ECS import ComponentNotRegisteredError, add_component_mapping, get_component_type
from tests.ECSTests import TestComponent, TestComponent2

logging.disable(logging.CRITICAL)


class ComponentMappingTestCase(unittest.TestCase):

    def setUp(self) -> None:
        ECS._component_mapping = {}

    def tearDown(self) -> None:
        ECS._component_mapping = {}

    def test_component_mapping(self):
        add_component_mapping(TestComponent)
        self.assertEqual(get_component_type(TestComponent.__name__), TestComponent)

        add_component_mapping(TestComponent)

        self.assertRaises(ComponentNotRegisteredError, get_component_type, TestComponent2.__name__)

    def test_multiple_component_mapping(self):
        add_component_mapping(TestComponent, TestComponent2)
        self.assertEqual(get_component_type(TestComponent.__name__), TestComponent)
        self.assertEqual(get_component_type(TestComponent2.__name__), TestComponent2)
