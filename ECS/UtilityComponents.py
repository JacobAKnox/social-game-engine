from typing import Self

from ECS import Component


class IntWrapper(Component):

    def __init__(self, data_: int):
        super().__init__()
        self.data = data_

    def __dict__(self):
        return {
            self.data_key(): self.data
        }

    def __eq__(self, other):
        if type(self) != type(other):
            return False
        return self.data == other.data

    @classmethod
    def from_dict(cls, data: dict) -> Self:
        return cls(data[cls.data_key()])

    @classmethod
    def data_key(cls) -> str:
        raise NotImplementedError
