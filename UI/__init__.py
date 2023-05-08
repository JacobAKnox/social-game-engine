import logging

import nextcord
from nextcord import Guild, CategoryChannel, Member, Role, PermissionOverwrite, TextChannel, Forbidden, \
    ApplicationError, Color
from nextcord.ext import commands, application_checks
from nextcord.ext.application_checks import ApplicationMissingPermissions

from UI.GameManagementCog import GameManagementCog
from UI.MessagingCog import MessagingCog
from UI.UserRegistrationCog import UserRegistrationCog
from UI.guild_ids import GUILD_IDS

logger = logging.getLogger(__name__)

_bot = commands.Bot()


def start_bot(token: str):
    _bot.run(token)


def setup_bot():
    # add cogs and whatnot here
    add_cogs()


def add_cogs():
    _bot.add_cog(MessagingCog())
    _bot.add_cog(UserRegistrationCog())
    _bot.add_cog(GameManagementCog())


EVERYONE_PERMS: PermissionOverwrite = PermissionOverwrite()
EVERYONE_PERMS.update(view_channel=False)

PLAYER_PERMS: PermissionOverwrite = PermissionOverwrite()
PLAYER_PERMS.update(view_channel=True, send_messages=True, manage_messages=True)


@_bot.event
async def on_ready():
    logger.info(f'We have logged in as {_bot.user}')


@_bot.event
async def on_application_command_error(interaction: nextcord.Interaction, error: ApplicationError):
    command = interaction.application_command
    if command == UserRegistrationCog.join or command == UserRegistrationCog.leave:
        await interaction.send("There is no game running in this server")
    elif isinstance(error, ApplicationMissingPermissions):
        await interaction.send("You do not have the required permissions to run this command")
    else:
        await interaction.send("Command failed for unknown reason. Please report this issue.")
        logger.error(f"Command failed for unknown reason")
        logger.error(f"{str(error)}")


@_bot.slash_command(description="Ping bot", guild_ids=GUILD_IDS)
async def ping(interaction: nextcord.Interaction):
    await interaction.send("Pong!")


@_bot.slash_command(description="Stop the bot", guild_ids=GUILD_IDS, )
@application_checks.is_owner()
async def stop(interaction: nextcord.Interaction):
    await interaction.send("Stopping...")
    logger.info("Stopping...")
    await _bot.close()


async def send_message(message: str, channel_id: int):
    channel = _bot.get_channel(channel_id)
    if channel is None:
        logger.warning(f"Failed to load channel with id: {channel_id}")
        return

    await channel.send(message)


async def get_guild(guild_id: int) -> Guild:
    guild: Guild = await _bot.fetch_guild(guild_id)
    if guild is None:
        raise KeyError(f"Bot is not in guild with id: {guild}")
    return guild


async def get_member(guild: Guild, member_id: int) -> Member:
    member: Member = await guild.fetch_member(member_id)
    if member is None:
        raise KeyError(f"Could not find member with id: {member_id}")
    return member


async def get_role(guild: Guild, role_id: int) -> Role:
    roles = await guild.fetch_roles()
    for role in roles:
        if role.id == role_id:
            return role
    raise KeyError(f"Guild {guild.id}, does not have role with id {role_id}")


@_bot.slash_command(description="test", guild_ids=GUILD_IDS)
async def test(interaction: nextcord.Interaction):
    role_id: int = 1089391851716485180
    guild: Guild = await _bot.fetch_guild(interaction.guild.id)
    await remove_role(interaction.user.id, guild.id, role_id)


async def make_role(name: str, guild: int) -> int:
    guild: Guild = await _bot.fetch_guild(guild)
    # color is a light blue hex #5FD0EB
    role: Role = await guild.create_role(name=name, color=Color.from_rgb(95, 208, 235), mentionable=True)
    logger.info(f"Created role with name: {name}")
    return role.id


async def delete_role(guild_id: int, role_id: int):
    guild: Guild = await _bot.fetch_guild(guild_id)
    roles = [r for r in await guild.fetch_roles() if r.id == role_id]
    if roles:
        logger.info(f"Deleting role with id {roles[0].id}")
        await roles[0].delete()


async def assign_role(user_id: int, guild_id: int, role_id: int):
    guild: Guild = await get_guild(guild_id)
    member: Member = await get_member(guild, user_id)
    role: Role = await get_role(guild, role_id)
    await member.add_roles(role)


async def remove_role(user_id: int, guild_id: int, role_id: int):
    guild: Guild = await get_guild(guild_id)
    member: Member = await get_member(guild, user_id)
    role: Role = await get_role(guild, role_id)
    await member.remove_roles(role)


async def make_player_channels(name: str, user_id: int, guild: int) -> tuple[int, int, int]:
    guild: Guild = await get_guild(guild)
    member: Member = await get_member(guild, user_id)
    everyone: Role = guild.default_role
    category: CategoryChannel = await guild.create_category(f"{name}",
                                                            overwrites={everyone: EVERYONE_PERMS,
                                                                        member: PLAYER_PERMS})
    info: TextChannel = await category.create_text_channel(f"{name}-info")
    command: TextChannel = await category.create_text_channel(f"{name}-commands")
    return info.id, command.id, category.id


async def remove_channels(guild: int, *channel_ids: int):
    guild: Guild = _bot.get_guild(guild)
    if guild is None:
        raise KeyError(f"Bot is not in guild with id: {guild}")
    for id_ in channel_ids:
        logger.info(f"Removing channel with id {id_}")
        channel = guild.get_channel_or_thread(id_)
        if channel is None:
            logger.error(f"Channel with id {id_} not found")
            continue
        try:
            await channel.delete()
        except Forbidden:
            logger.error(f"No permission to delete channel {channel.name}")
