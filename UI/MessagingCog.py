import logging

import nextcord
from nextcord.ext import commands

import Events
from Events import EventList as EventList
from UI.guild_ids import GUILD_IDS

logger = logging.getLogger(__name__)


class MessagingCog(commands.Cog):

    @nextcord.slash_command(description="Register the current channel", guild_ids=GUILD_IDS)
    async def register(self, interaction: nextcord.Interaction):
        channel_id = interaction.channel_id
        logger.info(f"Registered Channel with id: {channel_id}")
        await Events.EVENT_MANAGER.dispatch_event(EventList.REGISTER_CHANNEL_EVENT, channel_id=channel_id)
        await interaction.send("Registered channel")

    @nextcord.slash_command(description="sends a message", guild_ids=GUILD_IDS)
    async def send(self, interaction: nextcord.Interaction, message: str):
        logger.info(f"Sending '{message}' to registered channels")
        await Events.EVENT_MANAGER.dispatch_event(EventList.SEND_MESSAGE_EVENT, message=message)
        await interaction.send("Success")
