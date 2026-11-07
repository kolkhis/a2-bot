import os
import sys
import asyncio
import logging
import datetime as dt
import discord
from discord.ext import commands, tasks

from reminders import REMINDERS, TIMEZONE, DEFAULT_CHANNEL_ID

ALL_DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

BOT_TOKEN: str = os.environ.get('BOT_TOKEN', 'empty')
if BOT_TOKEN == 'empty':
    sys.stderr.write('[ERROR]: BOT_TOKEN environment variable is unset! Set in .env\n')
    sys.exit(1)

logging.basicConfig(level=logging.INFO, format="%(asctime)s:%(levelname)s:%(message)s")
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


bot: Bot = Bot()


def get_reminder_days(reminder: dict) -> list[str]:
    days = reminder.get("days", [])
    if "Daily" in days:
        return ALL_DAYS
    return days


def build_reminder_message(name: str, reminder: dict, reminder_dt: dt.datetime) -> str:
    role_id = reminder.get("role_id")
    mention = f"<@&{role_id}>" if role_id else ""
    message = reminder["message"].format(
        name=name,
        mention=mention,
        timestamp=discord.utils.format_dt(reminder_dt, style="t"),
        relative_timestamp=discord.utils.format_dt(reminder_dt, style="R"),
    )
    return message.strip()


async def get_text_channel(channel_id: int) -> discord.TextChannel | None:
    channel = bot.get_channel(channel_id)
    if channel is None:
        try:
            channel = await bot.fetch_channel(channel_id)
        except discord.HTTPException as e:
            log.error(f"Could not fetch channel {channel_id}: {e}")
            return None
    if not isinstance(channel, discord.TextChannel):
        return None
    return channel


###### COMMANDS ######
@bot.tree.command(name="reminders", description="Show the reminder schedule")
async def reminders_cmd(ita: discord.Interaction):
    embed = discord.Embed(
        title="Reminder Schedule",
        description="All times are shown in your local time.",
        color=discord.Color.gold(),
    )
    today = dt.datetime.now(TIMEZONE).date()
    for name, reminder in REMINDERS.items():
        reminder_time = dt.datetime.strptime(reminder["time"], "%H:%M").time()
        lines: list[str] = []
        for day in get_reminder_days(reminder):
            days_ahead = (ALL_DAYS.index(day) - today.weekday()) % 7
            reminder_dt = dt.datetime.combine(
                today + dt.timedelta(days=days_ahead), reminder_time, tzinfo=TIMEZONE
            )
            timestamp = discord.utils.format_dt(reminder_dt, style="t")
            lines.append(f"- **{day}** at {timestamp}" + (" **(today)**" if days_ahead == 0 else ""))
        embed.add_field(name=name, value="\n".join(lines) or "No days set", inline=False)
    await ita.response.send_message(embed=embed, ephemeral=True)


###### REMINDER LOOP ######
@tasks.loop(seconds=30)
async def reminder_loop():
    now = dt.datetime.now(TIMEZONE)
    current_day = now.strftime("%A")
    current_time = now.strftime("%H:%M")

    for name, reminder in REMINDERS.items():
        if current_day not in get_reminder_days(reminder) or reminder["time"] != current_time:
            continue

        key = (name, now.date(), current_time)
        if key in bot.sent_reminders:
            continue
        bot.sent_reminders.add(key)

        channel_id = reminder.get("channel_id", DEFAULT_CHANNEL_ID)
        channel = await get_text_channel(channel_id)
        if channel is None:
            log.error(f"Reminder '{name}' has no valid text channel ({channel_id}). Skipping.")
            continue

        reminder_dt = now.replace(second=0, microsecond=0)
        await channel.send(build_reminder_message(name, reminder, reminder_dt))
        log.info(f"Sent reminder '{name}' to #{channel.name}")

    # Drop keys from previous days so the set doesn't grow forever
    bot.sent_reminders = {k for k in bot.sent_reminders if k[1] == now.date()}

@reminder_loop.before_loop
async def before_reminder_loop():
    await bot.wait_until_ready()


async def main() -> None:
    async with bot:
        log.info("Bot starting...")
        if not reminder_loop.is_running():
            reminder_loop.start()
        await bot.start(BOT_TOKEN)


if __name__ == '__main__':
    asyncio.run(main())
