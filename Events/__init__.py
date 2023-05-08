import asyncio
import logging
from typing import Callable, Any, Awaitable

HANDLER_TYPE = Callable[[Any], Awaitable[Any]]

logger = logging.getLogger(__name__)


# modified from esper
# https://github.com/benmoran56/esper
class _EventManager:

    def __init__(self):
        self._subscribers: dict[str, set[HANDLER_TYPE]] = {}

    async def dispatch_event(self, name: str, *args, **kwargs) -> list[Any | BaseException]:
        calls = [func(*args, **kwargs) for func in self._subscribers.get(name, set())]
        # return is mostly for testing, but it may be useful later
        unsafe_results = list(await asyncio.gather(*calls, return_exceptions=True))
        results = []
        for r in unsafe_results:
            if isinstance(r, Exception):
                logger.error(f"Uncaught exception when processing event: {name}")
                logger.error(f"{str(r)}")
            else:
                results.append(r)

        return results

    def set_handler(self, name: str, func: HANDLER_TYPE) -> None:
        if name not in self._subscribers:
            self._subscribers[name] = set()

        self._subscribers[name].add(func)

    def remove_handler(self, name: str, func: HANDLER_TYPE) -> None:
        if func not in self._subscribers.get(name, []):
            return

        self._subscribers[name].remove(func)
        if not self._subscribers[name]:
            del self._subscribers[name]

    def clear(self):
        self._subscribers = {}


EVENT_MANAGER = _EventManager()
