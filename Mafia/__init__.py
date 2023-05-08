import logging
import uuid

import ECS
import Events.EventList
import Storage
from ECS import World
from ECS.ECSWrappers import query, query_entity_loop, query_component_loop, StopProcess, query_entity_component_loop
from Events.EventWrappers import check_argument
from Mafia.Channel import Guild, Channel, AnnouncementChannel, send_message, register_channel, PlayerRole, \
    delete_player_role, create_player_role
from Mafia.Game import GameMeta
from Mafia.User import DiscordUser, register_user, unregister_user, make_channels, check_user_exists, \
    remove_user_channels, add_player_role, remove_player_role

logger = logging.getLogger(__name__)


def register_mafia_components():  # pragma: no cover
    ECS.add_component_mapping(Guild)
    ECS.add_component_mapping(Channel)
    ECS.add_component_mapping(AnnouncementChannel)
    ECS.add_component_mapping(DiscordUser)
    ECS.add_component_mapping(GameMeta)
    ECS.add_component_mapping(PlayerRole)
    ECS.add_component_mapping(GameMeta)


def setup_world() -> World:  # pragma: no cover
    world_ = World()
    world_.register_processor_events(send_message, Events.EventList.SEND_MESSAGE_EVENT)
    world_.register_processor_events(register_channel, Events.EventList.REGISTER_CHANNEL_EVENT)
    world_.register_processor_events(register_user, Events.EventList.REGISTER_DISCORD_USER_EVENT)
    world_.register_processor_events(unregister_user, Events.EventList.UNREGISTER_DISCORD_USER_EVENT)
    world_.register_processor_events(create_game, Events.EventList.CREATE_GAME_EVENT)
    world_.register_processor_events(remove_game, Events.EventList.REMOVE_GAME_EVENT)
    world_.register_processor_events(remove_games, Events.EventList.REMOVE_ALL_GAMES_EVENT)
    world_.register_processor_events(game_exists, Events.EventList.CHECK_GAME_EXISTS)
    world_.register_processor_events(make_channels, Events.EventList.JOIN_USER)
    world_.register_processor_events(add_player_role, Events.EventList.JOIN_USER)
    world_.register_processor_events(check_user_exists, Events.EventList.CHECK_USER_EXIST)
    world_.register_processor_events(remove_user_channels, Events.EventList.LEAVE_USER)
    world_.register_processor_events(remove_player_role, Events.EventList.LEAVE_USER)
    world_.register_processor_events(delete_player_role, Events.EventList.PRE_REMOVE_GAME_EVENT)
    world_.register_processor_events(create_player_role, Events.EventList.PRE_CREATE_GAME_EVENT)
    world_.add_entities(*Storage.load_all_entities())
    return world_


@check_argument("guild", int)
@query("games", GameMeta, Guild)
async def create_game(world: World, *args, **kwargs):
    guild_id: int = kwargs["guild"]

    game_metas = kwargs["games"]
    if len(game_metas) > 0:
        logger.warning(f"{len(game_metas)} existing entities with a game meta found.")
        return False

    entity_id = world.add_components(None, GameMeta(), Guild(guild_id))
    await Events.EVENT_MANAGER.dispatch_event(Events.EventList.PRE_CREATE_GAME_EVENT, uuid=entity_id)
    logger.info(f"Created game in guild with id {guild_id}")
    return True


@query_entity_loop("games", sum, GameMeta)
async def remove_games(world: World, *args, **kwargs):
    entity_id = kwargs["games"]
    components = world.get_components(entity_id, GameMeta, Guild, PlayerRole)
    await Events.EVENT_MANAGER.dispatch_event(Events.EventList.PRE_REMOVE_GAME_EVENT, uuid=entity_id)
    world.remove_entity(entity_id)
    return 1


@check_argument("guild", int)
@query_entity_component_loop("games", any, GameMeta, Guild)
async def remove_game(world: World, *args, **kwargs):
    guild_id: int = kwargs["guild"]
    game_id: uuid = kwargs["games"][0]
    guild: Guild = kwargs["games"][1][Guild]

    if guild.data != guild_id:
        return

    components = world.get_components(game_id, GameMeta, Guild, PlayerRole)
    await Events.EVENT_MANAGER.dispatch_event(Events.EventList.PRE_REMOVE_GAME_EVENT, uuid=game_id)
    world.remove_entity(game_id)
    raise StopProcess(True)


@check_argument("guild", int)
@query_component_loop("games", any, GameMeta, Guild)
async def game_exists(world: World, *args, **kwargs):
    guild_id: int = kwargs["guild"]
    guild: Guild = kwargs["games"][Guild]
    if guild.data == guild_id:
        raise StopProcess(True)
