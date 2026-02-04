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
    "I was mining deep underground when a creeper exploded and scared me badly",
    "After exploring caves for a long time I finally found diamonds",
    "The village survived the raid because the iron golem fought bravely",
    "I entered the nether without preparation and learned my lesson quickly",
    "While building my base a skeleton kept shooting from far away",
    "The ender dragon fight became intense as endermen surrounded the area",
    "I spent the night protecting villagers from zombies and pillagers",
    "After falling into a ravine I escaped using water and blocks",
    "The redstone machine stopped working and flooded my underground base",
    "I traveled very far just to find a jungle biome",
    "I finally beat the game after many tries"
]

# ================= HELPERS =================
def reverse_sentence(sentence):
    return sentence[::-1]

def has_game_role():
    async def predicate(ctx):
        return any(role.id == GAME_MANAGER_ROLE_ID for role in ctx.author.roles)
    return commands.check(predicate)

# ================= DATABASE =================
conn = sqlite3.connect(DB_FILE, check_same_thread=False)
c = conn.cursor()

c.execute("CREATE TABLE IF NOT EXISTS points (user_id TEXT PRIMARY KEY, score INTEGER)")
c.execute("CREATE TABLE IF NOT EXISTS config (key TEXT PRIMARY KEY, value TEXT)")
conn.commit()

def add_point(user_id, amount=1):
    c.execute("SELECT score FROM points WHERE user_id = ?", (str(user_id),))
    row = c.fetchone()
    new_score = (row[0] if row else 0) + amount
    c.execute(
        "INSERT OR REPLACE INTO points (user_id, score) VALUES (?, ?)",
        (str(user_id), new_score)
    )
    conn.commit()
    return new_score

# ================= AUTO DM BACKUP =================
async def dm_leaderboard_backup():
    user = await bot.fetch_user(OWNER_ID)
    c.execute("SELECT user_id, score FROM points ORDER BY score DESC")
    rows = c.fetchall()

    if not rows:
        msg = "📊 Leaderboard Backup\n\n(No data)"
    else:
        msg = "📊 **Leaderboard Backup (Auto)**\n\n"
        for uid, score in rows:
            msg += f"{uid} : {score}\n"

    try:
        await user.send(msg)
    except:
        print("Could not DM leaderboard backup.")

# ================= ADMIN COMMANDS =================
@bot.command()
@commands.has_permissions(administrator=True)
async def givepoints(ctx, member: discord.Member, amount: int):
    new_score = add_point(member.id, amount)
    await ctx.send(f"✅ Added `{amount}` points to {member.mention} → Total: `{new_score}`")

@bot.command()
@commands.has_permissions(administrator=True)
async def bulkpoints(ctx, amount: int, *members: discord.Member):
    if not members:
        return await ctx.send("❌ Mention users to give points.")

    for member in members:
        add_point(member.id, amount)

    await ctx.send(f"✅ Added `{amount}` points to `{len(members)}` users.")

@bot.command()
@commands.has_permissions(administrator=True)
async def clearlb(ctx):
    c.execute("DELETE FROM points")
    conn.commit()
    await ctx.send("🗑️ Leaderboard cleared.")

# ================= GAME COMMANDS =================
@bot.command()
@has_game_role()
async def setgamechannel(ctx, channel: discord.TextChannel):
    c.execute(
        "INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)",
        ("game_channel", str(channel.id))
    )
    conn.commit()
    await ctx.send(f"🎮 Game channel set to {channel.mention}")

@bot.command()
@has_game_role()
async def startgame(ctx):
    global game_running, current_answer

    if game_running:
        return await ctx.send("⚠️ Game already running.")

    c.execute("SELECT value FROM config WHERE key = ?", ("game_channel",))
    row = c.fetchone()
    if not row:
        return await ctx.send("❌ Set a game channel first.")

    channel = ctx.guild.get_channel(int(row[0]))
    current_answer = random.choice(sentences)
    game_running = True

    await channel.send(
        f"🎮 **New Game Started!**\n"
        f"Reverse this sentence:\n`{reverse_sentence(current_answer)}`"
    )

@bot.command()
@has_game_role()
async def stopgame(ctx):
    global game_running, current_answer
    game_running = False
    current_answer = None
    await ctx.send("🛑 Game stopped.")

# ================= PUBLIC =================
@bot.command()
async def lb(ctx):
    c.execute("SELECT user_id, score FROM points ORDER BY score DESC LIMIT 10")
    rows = c.fetchall()

    if not rows:
        return await ctx.send("📭 Leaderboard is empty.")

    msg = "**🏆 TOP 10 LEADERBOARD**\n\n"
    for i, (uid, score) in enumerate(rows, 1):
        msg += f"**{i}.** <@{uid}> → `{score}`\n"

    await ctx.send(msg)

@bot.command()
async def help(ctx):
    await ctx.send(
        "**🤖 NEXUS COMMANDS**\n\n"
        "**👑 Admin**\n"
        "`*givepoints @user amount`\n"
        "`*bulkpoints amount @user @user`\n"
        "`*clearlb`\n\n"
        "**🎮 Game Manager**\n"
        "`*setgamechannel #channel`\n"
        "`*startgame`\n"
        "`*stopgame`\n\n"
        "**👤 Public**\n"
        "`*lb`\n"
        "`*help`"
    )

# ================= MESSAGE LISTENER =================
@bot.event
async def on_message(message):
    global game_running, current_answer
    if message.author.bot:
        return

    if game_running and current_answer:
        c.execute("SELECT value FROM config WHERE key = ?", ("game_channel",))
        row = c.fetchone()

        if row and message.channel.id == int(row[0]):
            norm = lambda t: re.sub(r"[^\w\s]", "", t.lower()).strip()

            if norm(message.content) == norm(current_answer):
                score = add_point(message.author.id)
                await message.channel.send(
                    f"🎉 {message.author.mention} WON! Total points: `{score}`"
                )

                game_running = False
                current_answer = None

                # 🔥 AUTO DM BACKUP
                await dm_leaderboard_backup()

    await bot.process_commands(message)

bot.run(TOKEN)
