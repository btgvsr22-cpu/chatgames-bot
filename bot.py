import os
import discord
from discord.ext import commands
from datetime import datetime, timezone
import random
import sqlite3

# ================= CONFIG =================
TOKEN = os.getenv("DISCORD_TOKEN")

VERIFIED_ROLE_ID = 1467128845093175397
NON_VERIFIED_ROLE_ID = 1467128749987336386

MIN_ACCOUNT_AGE_DAYS = 20
DB_FILE = "bot_data.db"
# =========================================

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="*", intents=intents, help_command=None)

# ================= GLOBALS =================
game_running = False
current_answer = None

sentences = [
    "creeper aw man",
    "never dig straight down",
    "minecraft is a sandbox game",
    "diamond armor is very rare",
    "the ender dragon lives in the end",
    "villagers trade emeralds",
    "nether portals need obsidian",
    "A creeper destroyed a massive redstone contraption underground",
    "The ender dragon was defeated after many failed attempts",
    "I lost all my items in lava after stepping in the nether",
    "A hidden stronghold was found deep underground",
    "The complex redstone system failed suddenly during a live stream",
    "I built a fully automated nether farm without getting detected",
    "The villager trader gave terrible trades that nobody enjoyed",
    "A lonely player survived the nether without armor",
    "The dangerous nether fortress almost made me die",
    "The wither boss destroyed the obsidian arena",
    "I crafted enchanted diamond armor",
    "A piston door failed during the raid",
    "Players escaped the nether fortress alive",
    "Redstone circuits powered the secret base",
    "The server crashed after massive lag",
    "The wither boss destroyed the obsidian arena underground",
    "I built a fully automated redstone contraption underground",
    "The ender dragon was defeated after many failed attempts",
    "A lonely player survived a long night in the nether",
    "The complex redstone system failed suddenly during a raid",
    "I lost all my items in lava after stepping in the nether",
    "The player built a hidden base underground",
    "A creeper exploded near the village",
    "The ender dragon destroyed the portal",
    "I lost all my items in lava",
    "Villagers offered terrible trades",
    "The player explored a deep cave full of mobs",
    "A wither boss spawned in the village",
    "The redstone contraption required precise timing",
    "I crafted a fully enchanted diamond pickaxe",
    "The nether portal broke during teleportation",
    "A piston door worked perfectly in the base",
    "The villager breeder produced good emeralds",
    "I lost my shield after fighting a skeleton",


]

def scramble_and_invert(sentence):
    return " ".join(sentence.split()[::-1])

# ================= DATABASE =================
conn = sqlite3.connect(DB_FILE, check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS points (
    user_id TEXT PRIMARY KEY,
    score INTEGER
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS config (
    key TEXT PRIMARY KEY,
    value TEXT
)
""")

conn.commit()

def safe_commit():
    try:
        conn.commit()
    except sqlite3.OperationalError:
        pass

def get_points(user_id):
    c.execute("SELECT score FROM points WHERE user_id = ?", (str(user_id),))
    row = c.fetchone()
    return row[0] if row else 0

def add_point(user_id):
    score = get_points(user_id) + 1
    c.execute(
        "INSERT OR REPLACE INTO points (user_id, score) VALUES (?, ?)",
        (str(user_id), score)
    )
    safe_commit()
    return score

def clear_points():
    c.execute("DELETE FROM points")
    safe_commit()

def save_config(key, value):
    c.execute(
        "INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)",
        (key, str(value))
    )
    safe_commit()

def load_config(key):
    c.execute("SELECT value FROM config WHERE key = ?", (key,))
    row = c.fetchone()
    return int(row[0]) if row else None

def save_message_id(msg_id):
    save_config("verify_message", msg_id)

# ================= GLOBAL ADMIN CHECK =================
@bot.check
async def admin_only(ctx):
    if ctx.guild is None:
        return False

    if ctx.author.guild_permissions.administrator:
        return True

    await ctx.reply(
        "🚫 **You don’t have permission to use this command.**\n"
        "🔒 Admin access required.",
        mention_author=False
    )
    return False

# ================= EVENTS =================
@bot.event
async def on_member_join(member):
    account_age = (datetime.now(timezone.utc) - member.created_at).days

    if account_age < MIN_ACCOUNT_AGE_DAYS:
        try:
            await member.ban(reason="Account too new (anti-alt)")
        except discord.Forbidden:
            pass
        return

    role = member.guild.get_role(NON_VERIFIED_ROLE_ID)
    if role:
        try:
            await member.add_roles(role)
        except discord.Forbidden:
            pass

# ================= VERIFICATION COMMAND =================
@bot.command()
async def setverifychannel(ctx, channel: discord.TextChannel):
    save_config("verify_channel", channel.id)
    await post_verify_panel(ctx.guild)
    await ctx.send(f"✅ Verification channel set to {channel.mention}")

# ================= CHAT GAME =================
@bot.command()
async def startgame(ctx):
    global game_running, current_answer

    if game_running:
        return await ctx.send("⚠️ A game is already running.")

    sentence = random.choice(sentences)
    current_answer = sentence.lower()
    game_running = True

    await ctx.send(
        f"🎮 **CHAT GAME**\n"
        f"Unscramble & fix the words:\n"
        f"🧩 `{scramble_and_invert(sentence)}`"
    )

@bot.event
async def on_message(message):
    global game_running, current_answer

    if message.author.bot:
        return

    if game_running and message.content.lower() == current_answer:
        game_running = False
        score = add_point(message.author.id)

        await message.channel.send(
            f"🏆 {message.author.mention} WON!\n"
            f"⭐ Points: {score}"
        )
        current_answer = None

    await bot.process_commands(message)

@bot.command()
async def leaderboard(ctx):
    c.execute("SELECT user_id, score FROM points ORDER BY score DESC LIMIT 10")
    rows = c.fetchall()

    if not rows:
        return await ctx.send("❌ No scores yet.")

    text = "🏆 **LEADERBOARD** 🏆\n"
    for i, (uid, score) in enumerate(rows, 1):
        try:
            user = await bot.fetch_user(int(uid))
            text += f"{i}. {user.name} — {score}\n"
        except:
            pass

    await ctx.send(text)

@bot.command()
async def clearleaderboard(ctx):
    clear_points()
    await ctx.send("🗑️ Leaderboard cleared.")

@bot.command()
async def stop(ctx):
    global game_running, current_answer
    game_running = False
    current_answer = None
    await ctx.send("🛑 Game stopped.")

# ================= POINT COMMANDS =================
@bot.command()
async def givepoints(ctx, member: discord.Member, amount: int):
    new_score = get_points(member.id) + amount
    c.execute(
        "INSERT OR REPLACE INTO points (user_id, score) VALUES (?, ?)",
        (str(member.id), new_score)
    )
    safe_commit()
    await ctx.send(f"✅ Added {amount} points to {member.mention}. New total: {new_score}")

@bot.command()
async def removepoints(ctx, member: discord.Member, amount: int):
    new_score = max(0, get_points(member.id) - amount)
    c.execute(
        "INSERT OR REPLACE INTO points (user_id, score) VALUES (?, ?)",
        (str(member.id), new_score)
    )
    safe_commit()
    await ctx.send(f"📉 Removed {amount} points from {member.mention}. New total: {new_score}")

@bot.command()
async def setpoints(ctx, member: discord.Member, amount: int):
    c.execute(
        "INSERT OR REPLACE INTO points (user_id, score) VALUES (?, ?)",
        (str(member.id), amount)
    )
    safe_commit()
    await ctx.send(f"🎯 Set {member.mention}'s points to {amount}")

# ================= HELP =================
@bot.command()
async def help(ctx):
    await ctx.send(
        "**📖 BOT COMMANDS (Admin Only)**\n\n"
        "**Verification**\n"
        "`*setverifychannel #channel` → Set verification channel\n\n"
        "**Chat Game**\n"
        "`*startgame` → Start game\n"
        "`*stop` → Stop game\n\n"
        "**Points**\n"
        "`*leaderboard`\n"
        "`*clearleaderboard`\n"
        "`*givepoints @user amount`\n"
        "`*removepoints @user amount`\n"
        "`*setpoints @user amount`\n\n"
        "🔒 Administrator permission required"
    )

# ================= ERROR HANDLER =================
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        return
    if isinstance(error, commands.BadArgument):
        await ctx.send("⚠️ Invalid arguments. Check `*help`.")
        return
    if isinstance(error, commands.CommandNotFound):
        return
    raise error

# ================= RUN =================
if not TOKEN:
    raise RuntimeError("DISCORD_TOKEN environment variable not set")

bot.run(TOKEN)

