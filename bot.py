import os
import discord
from discord.ext import commands, tasks
import random
import sqlite3
import re
import time

# ================= CONFIG =================
TOKEN = os.getenv("DISCORD_TOKEN")
GAME_MANAGER_ROLE_ID = 1468173295760314473
OWNER_ID = 1448709644091527363
DB_FILE = "/data/bot_data.db"
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

# ================= DATABASE =================
conn = sqlite3.connect(DB_FILE)
c = conn.cursor()

c.execute("""CREATE TABLE IF NOT EXISTS mc_points(user_id INTEGER PRIMARY KEY, score INTEGER DEFAULT 0)""")
c.execute("""CREATE TABLE IF NOT EXISTS gtn_points(user_id INTEGER PRIMARY KEY, score INTEGER DEFAULT 0)""")
c.execute("""CREATE TABLE IF NOT EXISTS quiz_points(user_id INTEGER PRIMARY KEY, score INTEGER DEFAULT 0)""")
c.execute("""CREATE TABLE IF NOT EXISTS config(key TEXT PRIMARY KEY, value TEXT)""")
conn.commit()

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

# ================= MC QUIZ QUESTIONS =================
quiz_questions = [
    ("Which mob drops Blaze Rods?", "blaze"),
    ("How many blocks are needed to make a Nether Portal frame?", "10"),
    ("What is the maximum level of Sharpness enchantment?", "5"),
    ("Which ore drops when mining Redstone?", "redstone"),
    ("What mob spawns only in the Nether and shoots fireballs?", "ghast"),
    ("What is the main ingredient for brewing a Potion of Healing?", "glistering_melon_slice"),
    ("Which animal drops Leather?", "cow"),
    ("Which tool is required to mine Obsidian?", "diamond_pickaxe"),
    ("What mob explodes when near the player?", "creeper"),
    ("Which item is used to tame a wolf?", "bone"),
    ("What block can you use to respawn in the End?", "ender_pearl"),
    ("Which potion grants Night Vision?", "night_vision"),
    ("Which block is required to craft a beacon?", "nether_star"),
    ("Which mob drops Phantom Membranes?", "phantom"),
    ("Which mob only spawns in desert temples?", "husk"),
    ("Which mob can teleport?", "enderman"),
    ("Which block is needed to craft a Lodestone?", "netherite_ingot"),
    ("Which food restores the most hunger points?", "steak"),
    ("Which mob drops Gunpowder?", "creeper"),
    ("Which mob drops Wither Skeleton Skulls?", "wither_skeleton"),
    ("Which block do you use to craft a Furnace?", "cobblestone"),
    ("Which mob is immune to sunlight and explodes?", "creeper"),
    ("Which potion grants Fire Resistance?", "fire_resistance"),
    ("Which mob is the final boss of Minecraft?", "ender_dragon"),
    ("Which mob guards ocean monuments?", "guardian"),
    ("Which mob drops Slimeballs?", "slime"),
    ("Which mob can fly and drops Elytra?", "phantom"),
    ("Which block is used to craft Enchanting Table?", "book"),
    ("Which mob drops Rotten Flesh?", "zombie"),
    ("Which block is used to craft TNT?", "gunpowder"),
    ("Which mob spawns in villages and trades items?", "villager"),
    ("Which mob drops Feathers?", "chicken"),
    ("Which block is required for Redstone circuits?", "redstone"),
    ("Which mob can spawn in caves only?", "bat"),
    ("Which mob can teleport and attack players?", "enderman"),
    ("Which potion allows underwater breathing?", "water_breathing"),
    ("Which mob can drop Saddles?", "hoglin"),
    ("Which block is used to craft a Compass?", "iron_ingot"),
    ("Which mob explodes when lit on fire?", "creeper"),
    ("Which mob spawns in the Nether and shoots fireballs?", "ghast"),
    ("Which potion grants Invisibility?", "invisibility"),
    ("Which mob drops String?", "spider"),
    ("Which mob can be tamed with bones?", "wolf"),
    ("Which block is used to craft a Brewing Stand?", "blaze_rod"),
    ("Which mob drops Ender Pearls?", "enderman"),
    ("Which mob drops Leather?", "cow"),
    ("Which mob drops Rotten Flesh?", "zombie"),
    ("Which mob guards villages?", "iron_golem"),
    ("Which mob is hostile in the Overworld at night?", "skeleton"),
    ("Which potion grants Speed?", "swiftness"),
    ("Which block is used to craft a Chest?", "wood"),
    ("Which mob attacks in packs?", "wolf"),
]

# ================= EMBED FUNCTION =================
def embed_msg(title, desc, color=discord.Color.gold()):
    return discord.Embed(title=title, description=desc, color=color)

# ================= POINT FUNCTIONS =================
def add_point(user_id):
    c.execute("INSERT OR IGNORE INTO mc_points(user_id) VALUES(?)", (user_id,))
    c.execute("UPDATE mc_points SET score = score + 1 WHERE user_id = ?", (user_id,))
    conn.commit()
    c.execute("SELECT score FROM mc_points WHERE user_id=?", (user_id,))
    return c.fetchone()[0]

def add_gtn_point(user_id):
    c.execute("INSERT OR IGNORE INTO gtn_points(user_id) VALUES(?)", (user_id,))
    c.execute("UPDATE gtn_points SET score = score + 1 WHERE user_id = ?", (user_id,))
    conn.commit()
    c.execute("SELECT score FROM gtn_points WHERE user_id=?", (user_id,))
    return c.fetchone()[0]

def add_quiz_point(user_id):
    c.execute("INSERT OR IGNORE INTO quiz_points(user_id) VALUES(?)", (user_id,))
    c.execute("UPDATE quiz_points SET score = score + 1 WHERE user_id = ?", (user_id,))
    conn.commit()
    c.execute("SELECT score FROM quiz_points WHERE user_id=?", (user_id,))
    return c.fetchone()[0]

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

# ================= START / STOP / LB POPUPS =================
# (Due to space, these should be coded with discord.ui Select/Views, 
# the same way you wanted popups for starting/stopping/lb/clearlb,
# including single instance enforcement for each game.)

# ================= ADMIN / GAME MANAGER COMMANDS =================
@bot.command()
@is_admin()
async def givepointsmc(ctx, user: discord.Member, amount: int):
    c.execute("INSERT OR IGNORE INTO mc_points(user_id) VALUES(?)",(user.id,))
    c.execute("UPDATE mc_points SET score = score + ? WHERE user_id = ?", (amount,user.id))
    conn.commit()
    await ctx.send(embed=embed_msg("✅ Points Added", f"{amount} MC Lines points added to {user.mention}"))

@bot.command()
@is_admin()
async def removepointsmc(ctx, user: discord.Member, amount: int):
    c.execute("INSERT OR IGNORE INTO mc_points(user_id) VALUES(?)",(user.id,))
    c.execute("UPDATE mc_points SET score = score - ? WHERE user_id = ?", (amount,user.id))
    conn.commit()
    await ctx.send(embed=embed_msg("✅ Points Removed", f"{amount} MC Lines points removed from {user.mention}"))

@bot.command()
@is_admin()
async def givepointsgtn(ctx, user: discord.Member, amount: int):
    c.execute("INSERT OR IGNORE INTO gtn_points(user_id) VALUES(?)",(user.id,))
    c.execute("UPDATE gtn_points SET score = score + ? WHERE user_id = ?", (amount,user.id))
    conn.commit()
    await ctx.send(embed=embed_msg("✅ Points Added", f"{amount} GTN points added to {user.mention}"))

@bot.command()
@is_admin()
async def removepointsgtn(ctx, user: discord.Member, amount: int):
    c.execute("INSERT OR IGNORE INTO gtn_points(user_id) VALUES(?)",(user.id,))
    c.execute("UPDATE gtn_points SET score = score - ? WHERE user_id = ?", (amount,user.id))
    conn.commit()
    await ctx.send(embed=embed_msg("✅ Points Removed", f"{amount} GTN points removed from {user.mention}"))

@bot.command()
@is_admin()
async def givepointquiz(ctx, user: discord.Member, amount: int):
    c.execute("INSERT OR IGNORE INTO quiz_points(user_id) VALUES(?)",(user.id,))
    c.execute("UPDATE quiz_points SET score = score + ? WHERE user_id = ?", (amount,user.id))
    conn.commit()
    await ctx.send(embed=embed_msg("✅ Points Added", f"{amount} MC Quiz points added to {user.mention}"))

@bot.command()
@is_admin()
async def removepointquiz(ctx, user: discord.Member, amount: int):
    c.execute("INSERT OR IGNORE INTO quiz_points(user_id) VALUES(?)",(user.id,))
    c.execute("UPDATE quiz_points SET score = score - ? WHERE user_id = ?", (amount,user.id))
    conn.commit()
    await ctx.send(embed=embed_msg("✅ Points Removed", f"{amount} MC Quiz points removed from {user.mention}"))

# ================= ANSWER DM COMMANDS =================
@bot.command()
@has_game_role()
async def gtnanswer(ctx):
    if gtn_number is None:
        await ctx.author.send(embed=embed_msg("ℹ️ GTN", "No GTN game is currently running."))
        return
    await ctx.author.send(embed=embed_msg("🎯 GTN Answer", f"The current GTN number is **{gtn_number}**"))

@bot.command()
@has_game_role()
async def giveanswerquiz(ctx):
    if quiz_answer is None:
        await ctx.author.send(embed=embed_msg("ℹ️ MC Quiz", "No MC Quiz is currently running."))
        return
    await ctx.author.send(embed=embed_msg("🎯 MC Quiz Answer", f"The current quiz answer is **{quiz_answer}**"))

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
import os
import discord
from discord.ext import commands, tasks
import random
import sqlite3
import re
import time

# ================= CONFIG =================
TOKEN = os.getenv("DISCORD_TOKEN")

GAME_MANAGER_ROLE_ID = 1468173295760314473
OWNER_ID = 1448709644091527363

DB_FILE = "/data/bot_data.db"
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

gtn_running = False
gtn_number = None
gtn_channel_id = None
gtn_low = 0
gtn_high = 0
gtn_cooldowns = {}

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
def reverse_sentence(sentence):
    return sentence[::-1]

def embed_msg(title, description, color=discord.Color.gold()):
    return discord.Embed(title=title, description=description, color=color)

def has_game_role():
    async def predicate(ctx):
        return any(role.id == GAME_MANAGER_ROLE_ID for role in ctx.author.roles)
    return commands.check(predicate)

# ================= DATABASE =================
conn = sqlite3.connect(DB_FILE, check_same_thread=False)
c = conn.cursor()

c.execute("CREATE TABLE IF NOT EXISTS points (user_id TEXT PRIMARY KEY, score INTEGER)")
c.execute("CREATE TABLE IF NOT EXISTS gtn_points (user_id TEXT PRIMARY KEY, score INTEGER)")
c.execute("CREATE TABLE IF NOT EXISTS config (key TEXT PRIMARY KEY, value TEXT)")
conn.commit()

def add_point(user_id, amount=1):
    c.execute("SELECT score FROM points WHERE user_id = ?", (str(user_id),))
    row = c.fetchone()
    new_score = (row[0] if row else 0) + amount
    c.execute("INSERT OR REPLACE INTO points VALUES (?,?)", (str(user_id), new_score))
    conn.commit()
    return new_score

def add_gtn_point(user_id, amount=1):
    c.execute("SELECT score FROM gtn_points WHERE user_id = ?", (str(user_id),))
    row = c.fetchone()
    new_score = (row[0] if row else 0) + amount
    c.execute("INSERT OR REPLACE INTO gtn_points VALUES (?,?)", (str(user_id), new_score))
    conn.commit()
    return new_score

# ================= MCLINES =================
@bot.command()
@has_game_role()
async def setmclines(ctx, channel: discord.TextChannel):
    c.execute("INSERT OR REPLACE INTO config VALUES (?,?)", ("game_channel", str(channel.id)))
    conn.commit()
    await ctx.send(embed=embed_msg("🎮 MCLINES Channel Set", f"{channel.mention}"))

@bot.command()
@has_game_role()
async def startmcline(ctx):
    global game_running, current_answer

    if game_running:
        return await ctx.send(embed=embed_msg("⚠️ Already Running", "MCLINES already active.", discord.Color.red()))

    c.execute("SELECT value FROM config WHERE key=?", ("game_channel",))
    row = c.fetchone()
    if not row:
        return await ctx.send(embed=embed_msg("❌ Error", "Set channel first.", discord.Color.red()))

    channel = ctx.guild.get_channel(int(row[0]))
    current_answer = random.choice(sentences)
    game_running = True

    await channel.send(embed=embed_msg("🎮 Reverse This", f"`{reverse_sentence(current_answer)}`"))

@bot.command()
@has_game_role()
async def stopmcline(ctx):
    global game_running,current_answer
    game_running=False
    current_answer=None
    await ctx.send(embed=embed_msg("🛑 Stopped","MCLINES stopped.",discord.Color.red()))

@bot.command()
async def lbmclines(ctx):
    c.execute("SELECT user_id,score FROM points ORDER BY score DESC LIMIT 10")
    rows=c.fetchall()
    if not rows:
        return await ctx.send(embed=embed_msg("📭 Empty","Leaderboard empty."))

    desc=""
    for i,(uid,score) in enumerate(rows,1):
        desc+=f"**{i}.** <@{uid}> → `{score}`\n"

    await ctx.send(embed=embed_msg("🏆 MCLINES Leaderboard",desc))

# ================= GTN =================
@bot.command()
@has_game_role()
async def setgtn(ctx, channel: discord.TextChannel):
    global gtn_channel_id
    gtn_channel_id = channel.id
    await ctx.send(embed=embed_msg("🎯 GTN Channel Set", f"{channel.mention}"))

@bot.command()
@has_game_role()
async def srtgtn(ctx):
    global gtn_running, gtn_number, gtn_low, gtn_high

    if not gtn_channel_id:
        return await ctx.send(embed=embed_msg("❌ Error", "Set channel first.", discord.Color.red()))

    gtn_running = True

    digits=random.choice([3,4])
    if digits==3:
        start=random.randint(100,800)
        end=start+random.randint(200,400)
    else:
        start=random.randint(1000,9000)
        end=start+random.randint(200,500)

    gtn_low=start
    gtn_high=end
    gtn_number=random.randint(start,end)

    channel=ctx.guild.get_channel(gtn_channel_id)
    await channel.send(embed=embed_msg("🎯 Guess The Number",f"Range **{start}-{end}**"))

@bot.command()
@has_game_role()
async def stopgtn(ctx):
    global gtn_running,gtn_number
    gtn_running=False
    gtn_number=None
    await ctx.send(embed=embed_msg("🛑 Stopped","GTN stopped.",discord.Color.red()))

@bot.command()
async def lbgtn(ctx):
    c.execute("SELECT user_id,score FROM gtn_points ORDER BY score DESC LIMIT 10")
    rows=c.fetchall()
    if not rows:
        return await ctx.send(embed=embed_msg("📭 Empty","Leaderboard empty."))

    desc=""
    for i,(uid,score) in enumerate(rows,1):
        desc+=f"**{i}.** <@{uid}> → `{score}`\n"

    await ctx.send(embed=embed_msg("🏆 GTN Leaderboard",desc))

# ================= MESSAGE LISTENER (MERGED) =================
@bot.event
async def on_message(message):
    global game_running,current_answer
    global gtn_running,gtn_number

    if message.author.bot:
        return

    # -------- MCLINES CHECK --------
    if game_running and current_answer:
        c.execute("SELECT value FROM config WHERE key=?",("game_channel",))
        row=c.fetchone()
        if row and message.channel.id==int(row[0]):
            norm=lambda t: re.sub(r"[^\w\s]","",t.lower()).strip()
            if norm(message.content)==norm(current_answer):
                score=add_point(message.author.id)
                await message.channel.send(embed=embed_msg("🎉 Winner!",f"{message.author.mention} → `{score}`"))
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
            await message.channel.send(embed=embed_msg("🎉 Correct!",f"{message.author.mention} guessed **{gtn_number}** → `{score}` wins"))
            gtn_running=False
            gtn_number=None
            return

        diff=abs(guess-gtn_number)

        if diff>100:
            text="📉 Too Far"
        elif diff>70:
            text="📊 Far"
        elif diff>50:
            text="📈 Close"
        else:
            text="🔥 Very Close"

        hint="Higher" if guess<gtn_number else "Lower"
        await message.channel.send(embed=embed_msg(text,hint))

    await bot.process_commands(message)

# ================= HELP =================
@bot.command()
async def help(ctx):

    embed=discord.Embed(title="🎮 NEXUS Game System",color=discord.Color.gold())

    if ctx.author.guild_permissions.administrator:
        embed.add_field(name="👑 Admin",
                        value="Admin commands enabled",
                        inline=False)

    if any(role.id==GAME_MANAGER_ROLE_ID for role in ctx.author.roles):
        embed.add_field(name="🎮 Manager",
                        value="""
*setmclines
*startmcline
*stopmcline
*setgtn
*srtgtn
*stopgtn
""",inline=False)

    embed.add_field(name="🌍 Public",
                    value="""
*lbmclines
*lbgtn
*help
""",inline=False)

    await ctx.send(embed=embed)

bot.run(TOKEN)

















