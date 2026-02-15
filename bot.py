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

# ================= DATABASE SETUP =================
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

# ================= ALL 45+ MCLINES SENTENCES =================
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

# ================= ADMIN COMMANDS =================
@bot.command()
@commands.has_permissions(administrator=True)
async def givepointsmc(ctx, member: discord.Member, amount: int):
    s = add_point(member.id, amount)
    await ctx.send(f"✅ Added {amount} MC points to {member.mention}. Total: {s}")

@bot.command()
@commands.has_permissions(administrator=True)
async def bulkpointsmc(ctx, amount: int):
    c.execute("UPDATE points SET score = score + ?", (amount,))
    conn.commit()
    await ctx.send(f"📈 Added {amount} MC points to EVERYONE in the database.")

@bot.command()
@commands.has_permissions(administrator=True)
async def givepointsgtn(ctx, member: discord.Member, amount: int):
    s = add_gtn_point(member.id, amount)
    await ctx.send(f"🎯 Added {amount} GTN points to {member.mention}. Total: {s}")

@bot.command()
@commands.has_permissions(administrator=True)
async def bulkpointsgtn(ctx, amount: int):
    c.execute("UPDATE gtn_points SET score = score + ?", (amount,))
    conn.commit()
    await ctx.send(f"📈 Added {amount} GTN points to EVERYONE in the database.")

@bot.command()
@commands.has_permissions(administrator=True)
async def removepointsmc(ctx, member: discord.Member, amount: int):
    s = add_point(member.id, -amount)
    await ctx.send(f"❌ Removed {amount} MC points from {member.mention}.")

@bot.command()
@commands.has_permissions(administrator=True)
async def removepointsgtn(ctx, member: discord.Member, amount: int):
    s = add_gtn_point(member.id, -amount)
    await ctx.send(f"❌ Removed {amount} GTN points from {member.mention}.")

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
    if game_running: return await ctx.send("⚠️ Game already running!")
    c.execute("SELECT value FROM config WHERE key = ?", ("game_channel",))
    row = c.fetchone()
    if not row: return await ctx.send("❌ Set channel first.")
    channel = bot.get_channel(int(row[0]))
    current_answer = random.choice(sentences)
    game_running = True
    await channel.send(embed=embed_msg("🎮 Reverse This", f"{reverse_sentence(current_answer)}"))

@bot.command()
@has_game_role()
async def stopmcline(ctx):
    global game_running; game_running = False
    await ctx.send("🛑 MCLINES stopped.")
@bot.command()
@has_game_role()
async def clearlbmclines(ctx):
    c.execute("DELETE FROM points")
    conn.commit()
    await ctx.send(embed=embed_msg("🧹 Reset", "MCLines Leaderboard wiped by Manager.", discord.Color.red()))
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
    if gtn_running: return await ctx.send("⚠️ GTN already running!")
    c.execute("SELECT value FROM config WHERE key = ?", ("gtn_channel",))
    row = c.fetchone()
    if row: gtn_channel_id = int(row[0])
    if not gtn_channel_id: return await ctx.send("❌ Set channel first.")
    gtn_running, gtn_number, gtn_low, gtn_high = True, random.randint(low, high), low, high
    await (bot.get_channel(gtn_channel_id)).send(embed=embed_msg("🎯 GTN Started!", f"Guess the number!"))

@bot.command()
@has_game_role()
async def hint(ctx):
    global gtn_running, gtn_low, gtn_high
    if not gtn_running: return
    rem = gtn_high - gtn_low
    if rem <= 15: return await ctx.send("⚠️ Too close for a hint!")
    await ctx.send(embed=embed_msg("🛰️ GTN Hint", f"Range: {gtn_low} - {gtn_high}"))

@bot.command()
@has_game_role()
async def gtnanswer(ctx):
    if gtn_running:
        try:
            await ctx.author.send(f"🤫 Answer: {gtn_number}")
            await ctx.message.add_reaction("✅")
        except: await ctx.send("❌ Open DMs!")

@bot.command()
@has_game_role()
async def stopgtn(ctx):
    global gtn_running; gtn_running = False
    await ctx.send("🛑 GTN stopped.")
@bot.command()
@has_game_role()
async def clearlbgtn(ctx):
    c.execute("DELETE FROM gtn_points")
    conn.commit()
    await ctx.send(embed=embed_msg("🧹 Reset", "GTN Leaderboard wiped by Manager.", discord.Color.red()))
# ================= MESSAGE LISTENER =================
@bot.event
async def on_message(message):
    global game_running, current_answer, gtn_running, gtn_number, gtn_low, gtn_high, gtn_channel_id
    if message.author.bot: return

    if game_running and current_answer:
        c.execute("SELECT value FROM config WHERE key = ?", ("game_channel",))
        row = c.fetchone()
        if row and message.channel.id == int(row[0]):
            norm = lambda t: re.sub(r"[^\w\s]", "", t.lower()).strip()
            if norm(message.content) == norm(current_answer):
                s = add_point(message.author.id)
                await message.channel.send(f"🎉 {message.author.mention} won! Total: {s}")
                game_running = False

    if gtn_running and message.channel.id == gtn_channel_id and message.content.isdigit():
        now = time.time()
        if now - gtn_cooldowns.get(message.author.id, 0) < 2: return
        gtn_cooldowns[message.author.id] = now
        guess = int(message.content)
        if guess == gtn_number:
            s = add_gtn_point(message.author.id)
            await message.channel.send(f"🎉 {message.author.mention} guessed {gtn_number}! Wins: {s}")
            gtn_running = False
        else:
            if guess < gtn_number: gtn_low = max(gtn_low, guess)
            else: gtn_high = min(gtn_high, guess)
            diff = abs(guess - gtn_number)
            if diff <= 10: txt, col = "🔥 RED HOT!", discord.Color.red()
            elif diff <= 50: txt, col = "✨ Very Close!", discord.Color.orange()
            elif diff <= 150: txt, col = "📈 Getting Closer...", discord.Color.gold()
            else: txt, col = "❄️ Cold.", discord.Color.blue()
            await message.channel.send(embed=embed_msg(txt, "Keep guessing!", col))
    # ================= QUIZ ANSWER CHECK =================
    global quiz_running, quiz_answer, quiz_channel_id
    if quiz_running and message.channel.id == quiz_channel_id:
        norm = lambda t: re.sub(r"[^\w\s]", "", t.lower()).strip()

        if norm(message.content) == norm(quiz_answer):
            s = add_quiz_point(message.author.id)

            await message.channel.send(embed=embed_msg(
                "🎉 Correct!",
                f"{message.author.mention} answered correctly!\nScore: **{s}**",
                discord.Color.green()
            ))

            q = random.choice(quiz_questions)
            quiz_answer = q[1]

            await message.channel.send(embed=embed_msg(
                "🧠 Next Question",
                q[0]
            ))

    await bot.process_commands(message)

# ================= LEADERBOARDS =================
@bot.command()
async def lbmclines(ctx):
    c.execute("SELECT user_id, score FROM points ORDER BY score DESC LIMIT 10")
    rows = c.fetchall()
    desc = "\n".join([f"**{i+1}.** <@{u}> — {s}" for i, (u, s) in enumerate(rows)])
    await ctx.send(embed=embed_msg("🏆 MCLINES Leaderboard", desc or "Empty"))

@bot.command()
async def lbgtn(ctx):
    c.execute("SELECT user_id, score FROM gtn_points ORDER BY score DESC LIMIT 10")
    rows = c.fetchall()
    desc = "\n".join([f"**{i+1}.** <@{u}> — {s}" for i, (u, s) in enumerate(rows)])
    await ctx.send(embed=embed_msg("🏆 GTN Leaderboard", desc or "Empty"))

# ================= HELP COMMAND (VERTICAL) =================
@bot.command()
async def help(ctx):
    embed = discord.Embed(title="🎮 NEXUS Game System", color=discord.Color.gold())
    
    is_admin = ctx.author.guild_permissions.administrator
    is_manager = any(role.id == GAME_MANAGER_ROLE_ID for role in ctx.author.roles)

    if is_admin:
        embed.add_field(name="👑 Admin Commands", value=(
            "• `*givepointsmc`\n"
            "• `*bulkpointsmc`\n"
            "• `*removepointsmc`\n"
            "• `*givepointsgtn`\n"
            "• `*bulkpointsgtn`\n"
            "• `*removepointsgtn`\n"
            "• `*givepointsquiz`\n"
            "• `*bulkpointsquiz`\n"
            "• `*removepointsquiz`\n"
        ), inline=False)

    if is_manager:
        embed.add_field(name="🛠️ Manager Commands", value=(
            "• `*setmclines #channel`\n"
            "• `*startmcline`\n"
            "• `*stopmcline`\n"
            "• `*clearlbmclines`\n"
            "• `*setgtn #channel`\n"
            "• `*srtgtn range`\n"
            "• `*stopgtn`\n"
            "• `*hint`\n"
            "• `*gtnanswer`\n"
            "• `*clearlbgtn`\n"
            "• `*setquiz #channel`\n"
            "• `*startquiz`\n"
            "• `*stopquiz`\n"
            "• `*clearquizlb`\n"
            
        ), inline=False)

    embed.add_field(name="🌍 Player Commands", value=(
        "• `*lbmclines`\n"
        "• `*lbgtn`\n"
        "• `*lbquiz`\n"
        "• `*help`"
    ), inline=False)
    
    await ctx.send(embed=embed)

# ================= GLOBAL GAME LOCK (ADD ONCE IN GLOBAL SECTION) =================
active_game = None

def start_game_lock(name):
    global active_game
    if active_game is not None:
        return False, active_game
    active_game = name
    return True, None

def stop_game_lock():
    global active_game
    active_game = None


# ================= QUIZ DATABASE =================
c.execute("CREATE TABLE IF NOT EXISTS quiz_points (user_id TEXT PRIMARY KEY, score INTEGER)")
conn.commit()


# ================= QUIZ GLOBALS =================
quiz_running = False
quiz_answer = None
quiz_channel_id = None


# ================= QUIZ QUESTIONS =================
quiz_questions = [
    ("Which mob drops gunpowder?", "creeper"),
    ("What ore is needed for netherite?", "ancient debris"),
    ("Which mob steals blocks?", "enderman"),
    ("Which item lets you fly?", "elytra"),
    ("Which boss lives in the End?", "ender dragon"),
    ("Which tool mines obsidian fastest?", "diamond pickaxe"),
    ("Which villager sells enchanted books?", "librarian"),
    ("Which block lets you set spawn?", "bed"),
    ("Which mob shoots fireballs?", "ghast"),
    ("What food do pandas eat?", "bamboo")
]


# ================= POINT SYSTEM =================
def add_quiz_point(user_id, amount=1):
    c.execute("SELECT score FROM quiz_points WHERE user_id=?", (str(user_id),))
    r = c.fetchone()
    score = (r[0] if r else 0) + amount
    c.execute("INSERT OR REPLACE INTO quiz_points VALUES (?,?)", (str(user_id), score))
    conn.commit()
    return score


# ================= COMMANDS =================
@bot.command()
@has_game_role()
async def setquiz(ctx, channel: discord.TextChannel):
    global quiz_channel_id
    quiz_channel_id = channel.id
    await ctx.send(embed=embed_msg("🧠 Quiz Channel Set", channel.mention))


@bot.command()
@has_game_role()
async def startquiz(ctx):
    global quiz_running, quiz_answer

    ok, running = start_game_lock("Minecraft Quiz")
    if not ok:
        return await ctx.send(embed=embed_msg(
            "⚠️ Game Running",
            f"A game is already running → **{running}**",
            discord.Color.red()
        ))

    if quiz_running:
        stop_game_lock()
        return await ctx.send(embed=embed_msg("⚠️ Already Running","Quiz already running",discord.Color.red()))

    if not quiz_channel_id:
        stop_game_lock()
        return await ctx.send(embed=embed_msg("❌ Error","Set channel first using *setquiz",discord.Color.red()))

    quiz_running = True
    q = random.choice(quiz_questions)
    quiz_answer = q[1]

    await bot.get_channel(quiz_channel_id).send(
        embed=embed_msg("🧠 Minecraft Quiz", q[0])
    )


@bot.command()
@has_game_role()
async def stopquiz(ctx):
    global quiz_running
    quiz_running = False
    stop_game_lock()
    await ctx.send(embed=embed_msg("🛑 Stopped","Quiz stopped.",discord.Color.red()))


@bot.command()
async def lbquiz(ctx):
    c.execute("SELECT user_id,score FROM quiz_points ORDER BY score DESC LIMIT 10")
    rows = c.fetchall()
    txt = "\n".join([f"**{i+1}.** <@{u}> — {s}" for i,(u,s) in enumerate(rows)])
    await ctx.send(embed=embed_msg("🏆 Quiz Leaderboard", txt or "Empty"))


@bot.command()
@has_game_role()
async def clearquizlb(ctx):
    c.execute("DELETE FROM quiz_points")
    conn.commit()
    await ctx.send(embed=embed_msg("🧹 Reset","Quiz leaderboard cleared.",discord.Color.red()))


@bot.command()
@commands.has_permissions(administrator=True)
async def givepointsquiz(ctx, member: discord.Member, amount:int):
    s = add_quiz_point(member.id, amount)
    await ctx.send(embed=embed_msg(
        "✅ Points Added",
        f"{member.mention} received **{amount}** points\nTotal: **{s}**"
    ))


@bot.command()
@commands.has_permissions(administrator=True)
async def removepointsquiz(ctx, member: discord.Member, amount:int):
    s = add_quiz_point(member.id, -amount)
    await ctx.send(embed=embed_msg(
        "❌ Points Removed",
        f"{member.mention} lost **{amount}** points\nTotal: **{s}**"
    ))


@bot.command()
@commands.has_permissions(administrator=True)
async def bulkpointsquiz(ctx, amount:int):
    c.execute("UPDATE quiz_points SET score = score + ?", (amount,))
    conn.commit()
    await ctx.send(embed=embed_msg(
        "📈 Bulk Added",
        f"Added **{amount}** quiz points to everyone."
    ))

bot.run(TOKEN)






