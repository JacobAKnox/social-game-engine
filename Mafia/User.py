import logging
import uuid
from typing import Self

import Events
import UI
from ECS import Component, World
from ECS.ECSWrappers import query_entity_component_loop, StopProcess, query
from Events import EventList
from Events.EventWrappers import check_argument
from Mafia import Guild, GameMeta
from Mafia.Channel import PlayerChannel, PlayerCommandChannel, PlayerCategory, PlayerRole, GameNotRunningException

logger = logging.getLogger(__name__)


class DiscordUser(Component):

    def __init__(self, user_id: int, display_name: str):
        super().__init__()
        self.discord_id = user_id
        self.display_name = display_name

    def __dict__(self):
        return {
            "discord_id": self.discord_id,
            "display_name": self.display_name
        }

    def __eq__(self, other):
        if type(self) != type(other):
            return False
        return self.discord_id == other.discord_id

    @classmethod
    def from_dict(cls, data: dict) -> Self:
        return cls(data["discord_id"], data["display_name"])


@check_argument("discord_id", int)
@check_argument("display_name", str)
async def register_user(world: World, *args, **kwargs):
    discord_id: int = kwargs.get("discord_id")
    display_name: str = kwargs.get("display_name")
    id_ = world.add_components(None, DiscordUser(discord_id, display_name))
    await Events.EVENT_MANAGER.dispatch_event(EventList.JOIN_USER, entity_id=id_)
    logger.info(f"Registered {display_name}")


@check_argument("entity_id", uuid.UUID)
@query("game", GameMeta, Guild)
async def make_channels(world: World, *args, **kwargs):
    user_id = kwargs["entity_id"]
    user: DiscordUser = world.get_components(user_id, DiscordUser)[DiscordUser]
    guild: Guild = world.get_components(list(kwargs["game"])[0], Guild)[Guild]
    channels = await UI.make_player_channels(user.display_name, user.discord_id, guild.data)
    world.add_components(user_id, PlayerChannel(channels[0]), PlayerCommandChannel(channels[1]),
                         PlayerCategory(channels[2]))


@check_argument("discord_id", int)
@query_entity_component_loop("users", any, DiscordUser)
async def unregister_user(world: World, *args, **kwargs):
    user_id = kwargs["users"][0]
    user: DiscordUser = kwargs["users"][1][DiscordUser]
    if user.discord_id == kwargs["discord_id"]:
        logger.info(f"Removing user {user.display_name}")
        await Events.EVENT_MANAGER.dispatch_event(EventList.LEAVE_USER, entity_id=user_id)
        world.remove_entity(user_id)
        raise StopProcess(True)
    return False


@check_argument("entity_id", uuid.UUID)
@query("game", GameMeta, Guild)
async def remove_user_channels(world: World, *args, **kwargs):
    entity = world.get_components(kwargs["entity_id"], PlayerChannel, PlayerCommandChannel, PlayerCategory)
    guild_id = world.get_components(list(kwargs["game"])[0], Guild)[Guild].data
    channels = []
    if PlayerCategory in entity:
        channels.append(entity[PlayerCategory].data)
    if PlayerChannel in entity:
        channels.append(entity[PlayerChannel].data)
    if PlayerCommandChannel in entity:
        channels.append(entity[PlayerCommandChannel].data)
    await UI.remove_channels(guild_id, *channels)


@check_argument("user", int)
@query_entity_component_loop("users", any, DiscordUser)
async def check_user_exists(world: World, *args, **kwargs):
    user_id = kwargs["user"]
    user: DiscordUser = kwargs["users"][1][DiscordUser]
    return user.discord_id == user_id


@check_argument("entity_id", uuid.UUID)
@query("game", GameMeta, Guild, PlayerRole)
async def add_player_role(world: World, *args, **kwargs):
    if len(kwargs["game"]) < 1:
        raise GameNotRunningException
    user_id = world.get_components(kwargs["entity_id"], DiscordUser)[DiscordUser].discord_id
    game_uuid = list(kwargs["game"])[0]
    game = world.get_components(game_uuid, Guild, PlayerRole)
    guild_id = game[Guild].data
    role_id = game[PlayerRole].data
    await UI.assign_role(user_id, guild_id, role_id)


@check_argument("entity_id", uuid.UUID)
@query("game", GameMeta, Guild, PlayerRole)
async def remove_player_role(world: World, *args, **kwargs):
    if len(kwargs["game"]) < 1:
        raise GameNotRunningException
    user_id = world.get_components(kwargs["entity_id"], DiscordUser)[DiscordUser].discord_id
    game_uuid = list(kwargs["game"])[0]
    game = world.get_components(game_uuid, Guild, PlayerRole)
    guild_id = game[Guild].data
    role_id = game[PlayerRole].data
    await UI.remove_role(user_id, guild_id, role_id)
