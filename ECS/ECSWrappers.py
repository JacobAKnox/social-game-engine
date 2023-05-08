import functools
import inspect
import logging
from typing import Any, Callable

from ECS import Component, World

logger = logging.getLogger(__name__)

WORLD_KEY = "world"


class InvalidParameterError(KeyError):
    pass


class StopProcess(Exception):
    def __init__(self, data: Any = None):
        self.data = data


def _check_world_argument(func) -> bool:
    annotations = inspect.get_annotations(func)

    if WORLD_KEY not in annotations:
        return False

    if annotations[WORLD_KEY] is not World:
        return False

    return True


def _extract_world(*args, **kwargs) -> World:
    if WORLD_KEY in kwargs:
        if isinstance(kwargs[WORLD_KEY], World):
            return kwargs[WORLD_KEY]

    for arg in args:
        if isinstance(arg, World):
            return arg

    raise KeyError("World argument not found")


def query(query_name: str, *components: type[Component]):
    def check_argument_wrapper(func):
        if not _check_world_argument(func):
            raise InvalidParameterError("Functions with the query decorator must have an argument \"world\" of type "
                                        "ECS.World")

        @functools.wraps(func)
        async def wrapper_decorator(*args, **kwargs):
            world = _extract_world(*args, **kwargs)
            query_result = world.query_components(*components)
            kwargs[query_name] = query_result
            return await func(*args, **kwargs)

        return wrapper_decorator

    return check_argument_wrapper


def query_component_loop(query_name: str, aggregator_func: Callable[[list], Any] = None, *components: type[Component]):
    def check_argument_wrapper(func):
        if not _check_world_argument(func):
            raise InvalidParameterError("Functions with the query decorator must have an argument \"world\" of type "
                                        "ECS.World")

        @functools.wraps(func)
        async def wrapper_decorator(*args, **kwargs):
            world = _extract_world(*args, **kwargs)
            component_list = [world.get_components(r, *components) for r in world.query_components(*components)]
            return await _query_loop(func, world, component_list, query_name, aggregator_func, *args, **kwargs)

        return wrapper_decorator

    return check_argument_wrapper


def query_entity_loop(query_name: str, aggregator_func: Callable[[list], Any] = None, *components: type[Component]):
    def check_argument_wrapper(func):
        if not _check_world_argument(func):
            raise InvalidParameterError("Functions with the query decorator must have an argument \"world\" of type "
                                        "ECS.World")

        @functools.wraps(func)
        async def wrapper_decorator(*args, **kwargs):
            world = _extract_world(*args, **kwargs)
            query_result = world.query_components(*components)
            return await _query_loop(func, world, query_result, query_name, aggregator_func, *args, **kwargs)

        return wrapper_decorator

    return check_argument_wrapper


def query_entity_component_loop(query_name: str, aggregator_func: Callable[[list], Any] = None,
                                *components: type[Component]):
    def check_argument_wrapper(func):
        if not _check_world_argument(func):
            raise InvalidParameterError("Functions with the query decorator must have an argument \"world\" of type "
                                        "ECS.World")

        @functools.wraps(func)
        async def wrapper_decorator(*args, **kwargs):
            world = _extract_world(*args, **kwargs)
            entities = ((id_, world.get_components(id_)) for id_ in world.query_components(*components))
            return await _query_loop(func, world, entities, query_name, aggregator_func, *args, **kwargs)

        return wrapper_decorator

    return check_argument_wrapper


async def _query_loop(func, world: World, query_, query_name: str,
                      aggregator: Callable[[list], Any] = None, *args, **kwargs):
    results = []
    for r in query_:
        kwargs[query_name] = r
        try:
            results.append(await func(world, *args, **kwargs))
        except StopProcess as e:
            if e.data is not None:
                results.append(e.data)
            break
    if aggregator is not None:
        return aggregator(results)
    return None
