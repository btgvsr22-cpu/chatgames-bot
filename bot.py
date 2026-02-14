import os
import discord
from discord.ext import commands
import random
import sqlite3
import re
import time

# ================= CONFIG =================
TOKEN = os.getenv("DISCORD_TOKEN")
GAME_MANAGER_ROLE_ID = 1468173295760314473
OWNER_ID = 1448709644091527363
DB_FILE = "/data/bot_data.db"

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix="*", intents=intents, help_command=None, activity=discord.Game(name="NEXUS Chat Game"))

# ================= DATABASE =================
conn = sqlite3.connect(DB_FILE, check_same_thread=False)
c = conn.cursor()
c.execute("""CREATE TABLE IF NOT EXISTS mc_points(user_id INTEGER PRIMARY KEY, score INTEGER DEFAULT 0)""")
c.execute("""CREATE TABLE IF NOT EXISTS gtn_points(user_id INTEGER PRIMARY KEY, score INTEGER DEFAULT 0)""")
c.execute("""CREATE TABLE IF NOT EXISTS quiz_points(user_id INTEGER PRIMARY KEY, score INTEGER DEFAULT 0)""")
c.execute("""CREATE TABLE IF NOT EXISTS config(key TEXT PRIMARY KEY, value TEXT)""")
conn.commit()

# ================= GLOBALS =================
game_running = False
current_answer = None

gtn_running = False
gtn_number = None
gtn_channel_id = None
gtn_low = 0
gtn_high = 0
gtn_cooldowns = {}

quiz_running = False
quiz_question = None
quiz_answer = None
quiz_channel_id = None
quiz_cooldowns = {}

# ================= MC LINES =================
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
]

# ================= MC QUIZ =================
quiz_questions = [
    ("Which mob drops Blaze Rods?", "blaze"),
    ("How many blocks are needed to make a Nether Portal frame?", "10"),
    ("What is the maximum level of Sharpness enchantment?", "5"),
    ("Which ore drops when mining Redstone?", "redstone"),
    ("What mob spawns only in the Nether and shoots fireballs?", "ghast"),
    # Add up to 50 hard/very hard questions
]

# ================= EMBED FUNCTION =================
def embed_msg(title, desc, color=discord.Color.gold()):
    return discord.Embed(title=title, description=desc, color=color)

# ================= POINT FUNCTIONS =================
def add_point(user_id):
    try:
        c.execute("INSERT OR IGNORE INTO mc_points(user_id) VALUES(?)", (user_id,))
        c.execute("UPDATE mc_points SET score = score + 1 WHERE user_id = ?", (user_id,))
        conn.commit()
        c.execute("SELECT score FROM mc_points WHERE user_id=?", (user_id,))
        return c.fetchone()[0]
    except:
        return 0

def add_gtn_point(user_id):
    try:
        c.execute("INSERT OR IGNORE INTO gtn_points(user_id) VALUES(?)", (user_id,))
        c.execute("UPDATE gtn_points SET score = score + 1 WHERE user_id = ?", (user_id,))
        conn.commit()
        c.execute("SELECT score FROM gtn_points WHERE user_id=?", (user_id,))
        return c.fetchone()[0]
    except:
        return 0

def add_quiz_point(user_id):
    try:
        c.execute("INSERT OR IGNORE INTO quiz_points(user_id) VALUES(?)", (user_id,))
        c.execute("UPDATE quiz_points SET score = score + 1 WHERE user_id = ?", (user_id,))
        conn.commit()
        c.execute("SELECT score FROM quiz_points WHERE user_id=?", (user_id,))
        return c.fetchone()[0]
    except:
        return 0

# ================= CHECK ROLES =================
def is_admin():
    async def predicate(ctx):
        return ctx.author.guild_permissions.administrator
    return commands.check(predicate)

def has_game_role():
    async def predicate(ctx):
        return any(role.id==GAME_MANAGER_ROLE_ID for role in ctx.author.roles)
    return commands.check(predicate)

# ================= CHANNEL SET COMMANDS =================
@bot.command()
@has_game_role()
async def setmclines(ctx, channel: discord.TextChannel):
    c.execute("INSERT OR REPLACE INTO config(key,value) VALUES(?,?)", ("mc_channel", str(channel.id)))
    conn.commit()
    await ctx.send(embed=embed_msg("✅ MC Lines Channel Set", f"{channel.mention} is now the MC Lines channel."))

@bot.command()
@has_game_role()
async def setgtn(ctx, channel: discord.TextChannel):
    c.execute("INSERT OR REPLACE INTO config(key,value) VALUES(?,?)", ("gtn_channel", str(channel.id)))
    conn.commit()
    await ctx.send(embed=embed_msg("✅ GTN Channel Set", f"{channel.mention} is now the GTN channel."))

@bot.command()
@has_game_role()
async def setquiz(ctx, channel: discord.TextChannel):
    c.execute("INSERT OR REPLACE INTO config(key,value) VALUES(?,?)", ("quiz_channel", str(channel.id)))
    conn.commit()
    await ctx.send(embed=embed_msg("✅ MC Quiz Channel Set", f"{channel.mention} is now the MC Quiz channel."))

# ================= MESSAGE LISTENER =================
@bot.event
async def on_message(message):
    global game_running,current_answer
    global gtn_running,gtn_number,gtn_channel_id
    global quiz_running, quiz_question, quiz_answer, quiz_channel_id

    if message.author.bot:
        return

    # -------- MCLINES CHECK --------
    if game_running and current_answer:
        c.execute("SELECT value FROM config WHERE key=?",("mc_channel",))
        row=c.fetchone()
        if row and message.channel.id==int(row[0]):
            norm=lambda t: re.sub(r"[^\w\s]","",t.lower()).strip()
            if norm(message.content)==norm(current_answer):
                score=add_point(message.author.id)
                await message.channel.send(embed=embed_msg("🎉 Winner!",f"{message.author.mention} → {score}"))
                game_running=False
                current_answer=None

    # -------- GTN CHECK --------
    if gtn_running and message.channel.id==gtn_channel_id and message.content.isdigit():
        now=time.time()
        last=gtn_cooldowns.get(message.author.id,0)
        if now-last<2:
            return
        gtn_cooldowns[message.author.id]=now
        guess=int(message.content)
        if guess==gtn_number:
            score=add_gtn_point(message.author.id)
            await message.channel.send(embed=embed_msg("🎉 Correct!",f"{message.author.mention} guessed **{gtn_number}** → {score} wins"))
            gtn_running=False
            gtn_number=None
            return
        diff=abs(guess-gtn_number)
        if diff>100: text="📉 Too Far"
        elif diff>70: text="📊 Far"
        elif diff>50: text="📈 Close"
        else: text="🔥 Very Close"
        hint="Higher" if guess<gtn_number else "Lower"
        await message.channel.send(embed=embed_msg(text,hint))

    # -------- MC QUIZ CHECK --------
    if quiz_running and message.channel.id==quiz_channel_id and quiz_answer:
        now=time.time()
        last=quiz_cooldowns.get(message.author.id,0)
        if now-last<2:
            return
        quiz_cooldowns[message.author.id]=now
        if message.content.lower().strip()==quiz_answer.lower().strip():
            score=add_quiz_point(message.author.id)
            await message.channel.send(embed=embed_msg("🎉 Correct!",f"{message.author.mention} → {score} points"))
            quiz_running=False
            quiz_question=None
            quiz_answer=None

    await bot.process_commands(message)

# ================= HELP =================
@bot.command()
async def help(ctx):
    embed=discord.Embed(title="🎮 NEXUS Game System", color=discord.Color.gold())
    if ctx.author.guild_permissions.administrator:
        embed.add_field(name="👑 Admin", value="""*givepointsmc @user amount
*removepointsmc @user amount
*bulkpointsmc amount @user1 @user2 ...
*givepointsgtn @user amount
*removepointsgtn @user amount
*bulkpointsgtn amount @user1 @user2 ...
*givepointquiz @user amount
*removepointquiz @user amount
*bulkpointquiz amount @user1 @user2 ...""", inline=False)
    if any(role.id==GAME_MANAGER_ROLE_ID for role in ctx.author.roles):
        embed.add_field(name="🎮 Manager", value="""*setmclines #channel
*setgtn #channel
*setquiz #channel
*srtgame
*stopgame
*lb
*clearlb
*gtnanswer
*giveanswerquiz""", inline=False)
    embed.add_field(name="🌍 Public", value="*help", inline=False)
    await ctx.send(embed=embed)

# ================= RUN BOT =================
bot.run(TOKEN)
