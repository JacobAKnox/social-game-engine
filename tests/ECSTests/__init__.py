from typing import Self

import ECS
from ECS import Component


def register_test_components():
    ECS.add_component_mapping(TestComponent)
    ECS.add_component_mapping(TestComponent2)


class TestComponent2(Component):

    def __init__(self):
        super().__init__()

    def __dict__(self):
        return {}

    def __eq__(self, other):
        if not isinstance(other, TestComponent2):
            return False
        return True

    @classmethod
    def from_dict(cls, data: dict) -> Self:
        return TestComponent2()


class TestComponent(Component):
    test_int: int
    test_str: str

    def __init__(self, num: int = 0, txt: str = 0):
        super().__init__()
        self.test_int = num
        self.test_str = txt

    def __dict__(self):
        return {
            "test_int": self.test_int,
            "test_str": self.test_str
        }

    def __eq__(self, other):
        if not isinstance(other, TestComponent):
            return False
        return self.test_str == other.test_str and self.test_int == other.test_int

    @classmethod
    def from_dict(cls, data: dict) -> Self:
        return TestComponent(data["test_int"], data["test_str"])


class UnusedTestComponent(Component):
    def __init__(self):
        super().__init__()

    def __dict__(self):
        return {}

    def __eq__(self, other):
        if not isinstance(other, UnusedTestComponent):
            return False
        return True

    @classmethod
    def from_dict(cls, data: dict) -> Self:
        return UnusedTestComponent()
