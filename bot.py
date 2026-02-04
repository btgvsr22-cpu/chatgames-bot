import os
import discord
from discord.ext import commands
import random
import sqlite3
import re

# ================= CONFIG =================
TOKEN = os.getenv("DISCORD_TOKEN")

GAME_MANAGER_ROLE_ID = 1468173295760314473
OWNER_ID = 1448709644091527363  # YOUR DISCORD ID

DB_FILE = "bot_data.db"
# =========================================

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(
    command_prefix="*",
    intents=intents,
    help_command=None,
    activity=discord.Game(name="NEXUS Chat Game")
)

# ================= GLOBALS =================
game_running = False
current_answer = None

# ================= SENTENCES =================
sentences = [
    "I was mining deep underground when a creeper exploded an
