import logging

import nextcord
from nextcord.ext import commands, application_checks

import Events
import Events.EventList as EventList
from UI.guild_ids import GUILD_IDS

logger = logging.getLogger(__name__)


class GameManagementCog(commands.Cog):

    @nextcord.slash_command(guild_ids=GUILD_IDS, description="Game Management command")
    async def game(self, interaction: nextcord.Interaction):
        await interaction.send("This command does nothing.\nTry one of the subcommands.")

    @game.subcommand(description="Create a game in this server")
    @application_checks.has_guild_permissions(administrator=True)
    async def create(self, interaction: nextcord.Interaction):
        guild_id = interaction.guild_id
        results = await Events.EVENT_MANAGER.dispatch_event(EventList.CREATE_GAME_EVENT, guild=guild_id)
        if not all(results):
            await interaction.send("Failed to create game, due to existing game")
            return
        await interaction.send("Game created!")

    @game.subcommand(description="Remove a game in this server")
    @application_checks.has_guild_permissions(administrator=True)
    async def remove(self, interaction: nextcord.Interaction):
        guild_id = interaction.guild_id
        results = await Events.EVENT_MANAGER.dispatch_event(EventList.REMOVE_GAME_EVENT, guild=guild_id)

        if not all(results):
            await interaction.send("Could not remove game in the server\n(maybe there wasn't one)")
            return

        await interaction.send("Removed game running in this server")

    @game.subcommand(description="Remove all games")
    @application_checks.is_owner()
    async def remove_all(self, interaction: nextcord.Interaction):
        results = await Events.EVENT_MANAGER.dispatch_event(EventList.REMOVE_ALL_GAMES_EVENT)
        total = sum(results)

        await interaction.send(f"Removed {total} game(s)")
