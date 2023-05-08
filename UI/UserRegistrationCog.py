import logging

import nextcord
from nextcord.ext import commands, application_checks

import Events
import Events.EventList as EventList
from UI.guild_ids import GUILD_IDS

logger = logging.getLogger(__name__)


def game_exists():  # pragma: no cover
    async def predicate(interaction: nextcord.Interaction):
        return any(await Events.EVENT_MANAGER.dispatch_event(EventList.CHECK_GAME_EXISTS, guild=interaction.guild_id))

    return application_checks.check(predicate)


async def user_check(id_: int):  # pragma: no cover
    return any(await Events.EVENT_MANAGER.dispatch_event(EventList.CHECK_USER_EXIST, user=id_))


class UserRegistrationCog(commands.Cog):

    @nextcord.slash_command(guild_ids=GUILD_IDS, description="Join the game!")
    @game_exists()
    async def join(self, interaction: nextcord.Interaction):
        discord_id = interaction.user.id
        display_name = interaction.user.display_name

        if await user_check(discord_id):
            await interaction.send("You are already in the game")
            return

        await Events.EVENT_MANAGER.dispatch_event(EventList.REGISTER_DISCORD_USER_EVENT,
                                                  discord_id=discord_id,
                                                  display_name=display_name)

        await interaction.send("Joined the game")

    @nextcord.slash_command(guild_ids=GUILD_IDS, description="Leave the game")
    @game_exists()
    async def leave(self, interaction: nextcord.Interaction):
        discord_id = interaction.user.id

        if not await user_check(discord_id):
            await interaction.send("You are not in the game")
            return

        if (await Events.EVENT_MANAGER.dispatch_event(EventList.UNREGISTER_DISCORD_USER_EVENT,
                                                      discord_id=discord_id))[0]:
            await interaction.send("Left the game")
        else:
            await interaction.send("Failed to remove you from the game\n(You may not have joined)")
