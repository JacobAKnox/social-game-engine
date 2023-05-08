import logging
import uuid

import UI
from ECS import World
from ECS.ECSWrappers import query_component_loop
from ECS.UtilityComponents import IntWrapper
from Events.EventWrappers import check_argument

logger = logging.getLogger(__name__)


class GameNotRunningException(Exception):
    pass


class PlayerRole(IntWrapper):
    @classmethod
    def data_key(cls) -> str:
        return "role_id"


class Guild(IntWrapper):  # pragma: no cover
    @classmethod
    def data_key(cls) -> str:
        return "guild_id"


class Channel(IntWrapper):  # pragma: no cover
    @classmethod
    def data_key(cls) -> str:
        return "channel_id"


class AnnouncementChannel(Channel):
    pass


class PlayerCategory(Channel):
    pass


class PlayerChannel(Channel):
    pass


class PlayerCommandChannel(Channel):
    pass


@check_argument("channel_id", int)
async def register_channel(world: World, *args, **kwargs):
    channel_id: int = kwargs["channel_id"]
    world.add_components(None, Channel(channel_id))


@check_argument("message", str)
@query_component_loop("channels", None, Channel)
async def send_message(world: World, *args, **kwargs):
    await UI.send_message(kwargs["message"], kwargs["channels"][Channel].data)


@check_argument("uuid", uuid.UUID)
async def delete_player_role(world: World, *args, **kwargs):
    components = world.get_components(kwargs["uuid"], Guild, PlayerRole)
    if PlayerRole not in components or Guild not in components:
        return
    await UI.delete_role(components[Guild].data, components[PlayerRole].data)


@check_argument("uuid", uuid.UUID)
async def create_player_role(world: World, *args, **kwargs):
    components = world.get_components(kwargs["uuid"], Guild)
    if Guild not in components:
        return
    world.add_components(kwargs["uuid"], PlayerRole(await UI.make_role("player", components[Guild].data)))
