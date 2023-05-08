import logging
import uuid
from typing import Self

from ECS import Component

logger = logging.getLogger(__name__)


class GameMeta(Component):

    def __init__(self, uuid_: int = 0):
        super().__init__()
        if uuid_ == 0:
            uuid_ = uuid.uuid4()
        else:
            try:
                uuid_ = uuid.UUID(int=uuid_, version=4)
            except ValueError:  # pragma: no cover
                logger.error(f"Tried to load invalid UUID: {uuid_}")
                uuid_ = uuid.uuid4()
        self.uuid = uuid_

    def __dict__(self):
        return {
            "id": self.uuid
        }

    def __eq__(self, other):
        if type(other) != type(self):
            return False
        return self.uuid == other.uuid

    @classmethod
    def from_dict(cls, data: dict) -> Self:
        return cls(int(data["id"]))
