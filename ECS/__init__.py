from __future__ import annotations

import logging
import uuid
from functools import partial
from typing import Optional, Self, TypeVar, Any, Callable, Awaitable

import Events
import Storage

logger = logging.getLogger(__name__)


class Component:
    def __init__(self):
        pass

    def __dict__(self):
        raise NotImplementedError

    def __eq__(self, other):
        raise NotImplementedError

    @classmethod
    def from_dict(cls, data: dict) -> Self:
        raise NotImplementedError


C = TypeVar("C", bound=Component)

_component_mapping: dict[str, type(C)] = {}


def add_component_mapping(*component_types: type(C)):
    for component_type in component_types:
        type_str = component_type.__name__
        if type_str not in _component_mapping.keys():
            _component_mapping[type_str] = component_type


def get_component_type(component: str) -> type(C):
    if component not in _component_mapping:
        raise ComponentNotRegisteredError
    return _component_mapping[component]


def int_to_uuid(uuid_: int) -> uuid:
    if uuid_ == 0:
        return uuid.uuid4()
    else:
        try:
            return uuid.UUID(int=uuid_, version=4)
        except ValueError:  # pragma: no cover
            logger.error(f"Tried to load invalid UUID: {uuid_}")
            return uuid.uuid4()


def unpack_components(*components: Component) -> dict[type[C], Component]:
    components_dict = {}
    for c in components:
        if type(c) not in components_dict:
            components_dict[type(c)] = c
    return components_dict


def entity_from_dict(data: dict) -> Optional[tuple[uuid, list[Component]]]:
    if "id" not in data:
        return None
    uuid_ = data.get("id")
    components = []
    for component_type, component_data in data.get("components").items():
        try:
            class_: type(C) = get_component_type(component_type)
            components.append(class_.from_dict(component_data))
        except ComponentNotRegisteredError:  # pragma: no cover
            logger.error(f"Tried to load unknown component type {component_type}")
            continue
    return uuid_, [*components]


def compare_entities(world: World, ent1: uuid, ent2: uuid):
    ent1_components = world.get_components(ent1)
    ent2_components = world.get_components(ent2)
    for component in ent1_components.values():
        if len([c for c in ent2_components.values() if component == c]) != 1:
            return False
    return True


class World:
    _entities: dict[uuid, dict[type[C], Component]] = None
    _components_cache: dict[type[C], set[uuid]] = None
    _events: dict[PROCESSOR_TYPE, (partial, set[str])] = None

    def __init__(self):
        self._entities = {}
        self._components_cache = {}
        self._events = {}

    def add_to_component_cache(self, uuid_: uuid, component: type[C]):
        if component not in self._components_cache:
            self._components_cache[component] = set()
        self._components_cache[component].add(uuid_)

    def remove_from_component_cache(self, uuid_: uuid, component: type[C]):
        if component not in self._components_cache:
            return
        if uuid_ not in self._components_cache[component]:
            return
        self._components_cache[component].remove(uuid_)

    # call with uuid_=None to make a new entity with a random uuid
    def add_components(self, uuid_: Optional[uuid], *components: Component) -> uuid.UUID:
        if uuid_ is None:
            uuid_ = uuid.uuid4()
        if uuid_ not in self._entities:
            self._entities[uuid_] = {}
        temp = self._entities[uuid_].copy()
        self._entities[uuid_] = unpack_components(*components)
        self._entities[uuid_].update(temp)
        for c in components:
            self.add_to_component_cache(uuid_, type(c))
        self.save_entity(uuid_)
        return uuid_

    def remove_components(self, uuid_: uuid, *components: type[C]) -> Optional[dict[type[C], C]]:
        if uuid_ not in self._entities:
            return None
        components_return = {}
        for c in components:
            if c not in self._components_cache:
                continue
            if uuid_ in self._components_cache[c]:
                components_return[c] = self._entities[uuid_].pop(c)
                self.remove_from_component_cache(uuid_, c)
        self.save_entity(uuid_)
        return components_return if components_return != {} else None

    def remove_entity(self, entity_id: uuid) -> Optional[dict[type[C], C]]:
        if entity_id not in self._entities:
            return None
        for c in self._entities.get(entity_id):
            self.remove_from_component_cache(entity_id, c)
        Storage.remove_entity(entity_id)
        return self._entities.pop(entity_id)

    def get_components(self, entity_id: uuid, *components: type[C]) -> Optional[dict[type[C], C]]:
        if entity_id not in self._entities:
            return None
        if len(components) == 0:
            return self._entities.get(entity_id)
        return {key: self._entities.get(entity_id).get(key)
                for key in self._entities.get(entity_id) if key in components}

    def save_entity(self, entity_id: uuid):
        if entity_id not in self._entities:
            logger.error(f"Tried to save entity that does not exist. id: {entity_id}")
            return
        Storage.save_entity(self.get_entity_data(entity_id))

    def get_entity_data(self, entity_id: uuid) -> Optional[dict]:
        if entity_id not in self._entities:
            return None
        return {
            "id": entity_id,
            "components": {
                type(comp).__name__: comp.__dict__() for comp in self._entities.get(entity_id).values()
            }
        }

    def has_entity(self, entity_id: uuid) -> bool:
        return entity_id in self._entities

    def register_processor_events(self, processor: PROCESSOR_TYPE, *events: str):
        part = partial(self.run_processor, processor)
        if processor not in self._events:
            self._events[processor] = (part, set())
        for e in events:
            self._events[processor][1].add(e)  # [1] accesses the set [0] is the partial function
            Events.EVENT_MANAGER.set_handler(e, part)

    def unregister_processor_events(self, processor: PROCESSOR_TYPE):
        if processor not in self._events:
            return
        part = self._events[processor][0]
        for e in self._events[processor][1]:
            Events.EVENT_MANAGER.remove_handler(e, part)
        del self._events[processor]

    async def run_processor(self, processor: PROCESSOR_TYPE, *args, **kwargs) -> Any:
        return await processor(self, *args, **kwargs)

    def query_components(self, *components: type[C]) -> set[uuid]:
        for c in components:
            if c not in self._components_cache:
                self._components_cache[c] = set()
        return set.intersection(*(self._components_cache.get(c) for c in components))

    def add_entities(self, *data: dict):
        for e in data:
            unpacked = entity_from_dict(e)
            if unpacked is None:
                continue
            self.add_components(unpacked[0], *(unpacked[1]))


PROCESSOR_TYPE = Callable[[World, Any], Awaitable[Any]]


class ComponentNotRegisteredError(KeyError):
    pass
