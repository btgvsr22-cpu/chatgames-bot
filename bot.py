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

bot = commands.Bot(
    command_prefix="*",
    intents=intents,
    help_command=None,
    activity=discord.Game(name="NEXUS Chat Games")
)

# ================= DATABASE =================
conn = sqlite3.connect(DB_FILE, check_same_thread=False)
c = conn.cursor()
c.execute("CREATE TABLE IF NOT EXISTS points (user_id TEXT PRIMARY KEY, score INTEGER)")
c.execute("CREATE TABLE IF NOT EXISTS gtn_points (user_id TEXT PRIMARY KEY, score INTEGER)")
c.execute("CREATE TABLE IF NOT EXISTS config (key TEXT PRIMARY KEY, value TEXT)")
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

# ================= ALL 20 MCLINES SENTENCES (RESTORED) =================
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
    "While building a bridge in the nether I almost fell into lava",
    "The stronghold was hidden so deep that it took hours to find",
    "I tried speedrunning but a creeper ended the run instantly",
    "During the raid multiple evokers spawned and caused confusion",
    "I lost my enchanted armor while fighting wither skeletons",
    "The ocean monument felt dangerous with guardians attacking constantly",
    "I built a farm but forgot to light it properly",
    "After curing villagers I finally unlocked good trades",
    "The end city loot was worth the risky elytra flight",
    "I entered a cave thinking it was safe but mobs kept spawning",
    "While exploring the nether fortress I got surrounded by blazes",
    "I survived my hardcore world for weeks before one mistake",
    "The piston door broke during a redstone test",
    "I tried escaping lava by placing blocks quickly",
    "The village bell rang loudly as the raid started",
    "I spent hours organizing chests and still felt lost",
    "Mining ancient debris took patience and careful planning",
    "I lost my elytra durability mid flight and panicked",
    "The beacon effects made mining much faster",
    "I built a secret underground base with long tunnels",
    "The night felt endless as phantoms kept attacking",
    "I trapped a villager to get mending books",
    "The nether highway saved time but felt unsafe",
    "I explored a deep dark biome and felt nervous",
    "The warden sounds echoed through the cave",
    "I fought the wither and damaged half my base",
    "The redstone clock failed and broke the system",
    "I fought the dragon without enough preparation",
    "The mineshaft was full of webs and spiders",
    "I built a castle but never finished decorating it",
    "I survived a fall by placing water quickly",
    "The bastion loot was guarded by piglin brutes",
    "I underestimated the raid difficulty and struggled",
    "I spent days farming netherite upgrades",
    "Flying with elytra felt risky but exciting",
    "The villagers panicked as zombies attacked",
    "I explored a snowy biome for resources",
    "I finally beat the game after many tries"
]

# ================= HELPERS =================
def reverse_sentence(sentence): return sentence[::-1]
def embed_msg(title, description, color=discord.Color.gold()): return discord.Embed(title=title, description=description, color=color)
def has_game_role():
    async def predicate(ctx): return any(role.id == GAME_MANAGER_ROLE_ID for role in ctx.author.roles)
    return commands.check(predicate)

def add_point(user_id, amount=1):
    c.execute("SELECT score FROM points WHERE user_id = ?", (str(user_id),))
    row = c.fetchone()
    new_score = (row[0] if row else 0) + amount
    c.execute("INSERT OR REPLACE INTO points (user_id, score) VALUES (?, ?)", (str(user_id), new_score))
    conn.commit()
    return new_score

def add_gtn_point(user_id, amount=1):
    c.execute("SELECT score FROM gtn_points WHERE user_id = ?", (str(user_id),))
    row = c.fetchone()
    new_score = (row[0] if row else 0) + amount
    c.execute("INSERT OR REPLACE INTO gtn_points (user_id, score) VALUES (?, ?)", (str(user_id), new_score))
    conn.commit()
    return new_score

# ================= MCLINES COMMANDS =================
@bot.command()
@has_game_role()
async def setmclines(ctx, channel: discord.TextChannel):
    c.execute("INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)", ("game_channel", str(channel.id)))
    conn.commit()
    await ctx.send(embed=embed_msg("🎮 MCLINES Channel Set", f"{channel.mention}"))

@bot.command()
@has_game_role()
async def startmcline(ctx):
    global game_running, current_answer
    if game_running: return await ctx.send(embed=embed_msg("⚠️ Active", "An MCLINES game is already running!", discord.Color.red()))
    c.execute("SELECT value FROM config WHERE key = ?", ("game_channel",))
    row = c.fetchone()
    if not row: return await ctx.send("❌ Set MCLINES channel first.")
    channel = bot.get_channel(int(row[0]))
    current_answer = random.choice(sentences)
    game_running = True
    await channel.send(embed=embed_msg("🎮 Reverse This", f"{reverse_sentence(current_answer)}"))

@bot.command()
@has_game_role()
async def stopmcline(ctx):
    global game_running, current_answer
    game_running, current_answer = False, None
    await ctx.send(embed=embed_msg("🛑 Stopped", "MCLINES stopped.", discord.Color.red()))

# ================= GTN COMMANDS =================
@bot.command()
@has_game_role()
async def setgtn(ctx, channel: discord.TextChannel):
    c.execute("INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)", ("gtn_channel", str(channel.id)))
    conn.commit()
    await ctx.send(embed=embed_msg("🎯 GTN Channel Set", f"{channel.mention}"))

@bot.command()
@has_game_role()
async def srtgtn(ctx, low: int = 0, high: int = 1000):
    global gtn_running, gtn_number, gtn_low, gtn_high, gtn_channel_id
    if gtn_running: return await ctx.send(embed=embed_msg("⚠️ Active", "A GTN game is already running!", discord.Color.red()))
    c.execute("SELECT value FROM config WHERE key = ?", ("gtn_channel",))
    row = c.fetchone()
    if row: gtn_channel_id = int(row[0])
    if not gtn_channel_id: return await ctx.send("❌ Set GTN channel first.")
    gtn_running, gtn_number, gtn_low, gtn_high = True, random.randint(low, high), low, high
    channel = bot.get_channel(gtn_channel_id)
    await channel.send(embed=embed_msg("🎯 GTN Started!", f"Guess the number between **{low}** and **{high}**!"))

@bot.command()
@has_game_role()
async def hint(ctx):
    global gtn_running, gtn_low, gtn_high
    if not gtn_running: return await ctx.send("❌ No active game.")
    remaining = gtn_high - gtn_low
    if remaining <= 15: return await ctx.send("⚠️ Range is too narrow for a hint!")
    await ctx.send(embed=embed_msg("🛰️ GTN Hint", f"Range: **{gtn_low}** — **{gtn_high}**\nLeft: `{remaining}`"))

@bot.command()
@has_game_role()
async def gtnanswer(ctx):
    global gtn_running, gtn_number
    if not gtn_running: return await ctx.send("❌ No active game.")
    try:
        await ctx.author.send(embed=embed_msg("🤫 Answer", f"The number is: **{gtn_number}**"))
        await ctx.message.add_reaction("✅")
    except: await ctx.send("❌ Open your DMs!")

@bot.command()
@has_game_role()
async def stopgtn(ctx):
    global gtn_running, gtn_number
    gtn_running, gtn_number = False, None
    await ctx.send(embed=embed_msg("🛑 Stopped", "GTN stopped.", discord.Color.red()))

# ================= LEADERBOARDS =================
@bot.command()
async def lbmclines(ctx):
    c.execute("SELECT user_id, score FROM points ORDER BY score DESC LIMIT 10")
    rows = c.fetchall()
    desc = "\n".join([f"*{i+1}.* <@{uid}> → {score}" for i, (uid, score) in enumerate(rows)])
    await ctx.send(embed=embed_msg("🏆 MCLINES Leaderboard", desc or "Empty"))

@bot.command()
async def lbgtn(ctx):
    c.execute("SELECT user_id, score FROM gtn_points ORDER BY score DESC LIMIT 10")
    rows = c.fetchall()
    desc = "\n".join([f"*{i+1}.* <@{uid}> → {score}" for i, (uid, score) in enumerate(rows)])
    await ctx.send(embed=embed_msg("🏆 GTN Leaderboard", desc or "Empty"))

# ================= MESSAGE LISTENER =================
@bot.event
async def on_message(message):
    global game_running, current_answer, gtn_running, gtn_number, gtn_low, gtn_high, gtn_channel_id
    if message.author.bot: return

    # MCLINES CHECK
    if game_running and current_answer:
        c.execute("SELECT value FROM config WHERE key = ?", ("game_channel",))
        row = c.fetchone()
        if row and message.channel.id == int(row[0]):
            norm = lambda t: re.sub(r"[^\w\s]", "", t.lower()).strip()
            if norm(message.content) == norm(current_answer):
                score = add_point(message.author.id)
                await message.channel.send(embed=embed_msg("🎉 Winner!", f"{message.author.mention} scored! Total: {score}"))
                game_running, current_answer = False, None

    # GTN CHECK
    if gtn_running and message.channel.id == gtn_channel_id and message.content.isdigit():
        now = time.time()
        if now - gtn_cooldowns.get(message.author.id, 0) < 2: return
        gtn_cooldowns[message.author.id] = now
        guess = int(message.content)
        if guess == gtn_number:
            score = add_gtn_point(message.author.id)
            await message.channel.send(embed=embed_msg("🎉 Correct!", f"{message.author.mention} won! Total: {score}"))
            gtn_running, gtn_number = False, None
            return
        if guess < gtn_number: gtn_low = max(gtn_low, guess)
        elif guess > gtn_number: gtn_high = min(gtn_high, guess)
        diff = abs(guess - gtn_number)
        if diff <= 10: text, col = "🔥 RED HOT!", discord.Color.red()
        elif diff <= 50: text, col = "✨ Very Close!", discord.Color.orange()
        elif diff <= 150: text, col = "📈 Getting Closer...", discord.Color.gold()
        else: text, col = "❄️ Cold.", discord.Color.blue()
        await message.channel.send(embed=embed_msg(text, "Keep guessing!", col))

    await bot.process_commands(message)

# ================= HELP =================
@bot.command()
async def help(ctx):
    embed = discord.Embed(title="🎮 NEXUS Game System", color=discord.Color.gold())
    is_m = any(role.id == GAME_MANAGER_ROLE_ID for role in ctx.author.roles)
    if is_m:
        embed.add_field(name="🛠️ Manager", value="`*setmclines`, `*startmcline`, `*stopmcline`\n`*setgtn`, `*srtgtn`, `*stopgtn`, `*hint`, `*gtnanswer` ", inline=False)
    embed.add_field(name="🌍 Public", value="`*lbmclines`, `*lbgtn`, `*help` ", inline=False)
    await ctx.send(embed=embed)

bot.run(TOKEN)
