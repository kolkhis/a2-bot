import logging
import datetime as dt
import discord
from discord.ext import commands

log = logging.getLogger("heaven")


class Bot(commands.Bot):
    def __init__(self) -> None:
        intents: discord.Intents = discord.Intents.default()
        super().__init__(command_prefix="!", intents=intents)
        # Tracks (reminder name, date, time) already sent, so a reminder can't fire twice
        self.sent_reminders: set[tuple[str, dt.date, str]] = set()

    async def setup_hook(self) -> None:
        await self.tree.sync()
        log.info("Slash commands synced.")

    async def on_ready(self) -> None:
        log.info(f"Logged in as {self.user} (ID: {self.user.id if self.user else '?'})")
