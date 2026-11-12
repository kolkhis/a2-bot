# Reminder schedule definitions.
# Edit this file to add, remove, or change reminders.

import os
from zoneinfo import ZoneInfo

# All reminder times below are interpreted in this timezone
TIMEZONE = ZoneInfo(os.environ.get("REMINDER_TZ", "America/New_York"))

# Channel reminders are posted to when a reminder doesn't set its own `channel_id`
DEFAULT_CHANNEL_ID: int = int(os.environ.get("REMINDER_CHANNEL_ID", "0"))

# Each reminder:
#   days:       list of weekday names ("Monday" .. "Sunday"), or ["Daily"]
#   time:       "HH:MM" (24-hour, in TIMEZONE)
#   message:    text to post. Supports {name}, {mention}, {timestamp}, {relative_timestamp}
#   channel_id: (optional) channel to post in, overrides DEFAULT_CHANNEL_ID
#   role_id:    (optional) role to ping via {mention}
REMINDERS: dict[str, dict] = {
    "Weekly Reset": {
        "days": ["Tuesday"],
        "time": "12:00",
        "message": "{mention} Reminder: **Weekly reset is tomorrow.** Make sure " \
        "you do your Ascension trials and weekly commands!",
    },
}
