import os
import discord
from discord.ext import commands, tasks
import random
import sqlite3
import re

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
gtn_high = 9999

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

# ================= MCLINES =================
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
    if game_running:
        return await ctx.send(embed=embed_msg("⚠️ Already Running", "MCLINES is already active.", discord.Color.red()))

    c.execute("SELECT value FROM config WHERE key = ?", ("game_channel",))
    row = c.fetchone()
    if not row:
        return await ctx.send(embed=embed_msg("❌ Error", "Set a MCLINES channel first.", discord.Color.red()))

    channel = ctx.guild.get_channel(int(row[0]))
    current_answer = random.choice(sentences)
    game_running = True

    await channel.send(embed=embed_msg("🎮 Reverse This", f"`{reverse_sentence(current_answer)}`"))

@bot.command()
@has_game_role()
async def stopmcline(ctx):
    global game_running, current_answer
    game_running = False
    current_answer = None
    await ctx.send(embed=embed_msg("🛑 Stopped", "MCLINES stopped.", discord.Color.red()))

@bot.command()
@has_game_role()
async def clearlbmclines(ctx):
    c.execute("DELETE FROM points")
    conn.commit()
    await ctx.send(embed=embed_msg("🗑️ Cleared", "MCLINES leaderboard cleared."))

@bot.command()
async def lbmclines(ctx):
    c.execute("SELECT user_id, score FROM points ORDER BY score DESC LIMIT 10")
    rows = c.fetchall()
    if not rows:
        return await ctx.send(embed=embed_msg("📭 Empty", "Leaderboard is empty."))

    desc = ""
    for i, (uid, score) in enumerate(rows, 1):
        desc += f"**{i}.** <@{uid}> → `{score}`\n"

    await ctx.send(embed=embed_msg("🏆 MCLINES Leaderboard", desc))

# ================= ADMIN POINT CONTROL - MCLINES =================
@bot.command()
async def givepointsmc(ctx, member: discord.Member, amount: int):
    if not ctx.author.guild_permissions.administrator:
        return await ctx.send(embed=embed_msg("❌ No Permission", "Admin only command.", discord.Color.red()))

    score = add_point(member.id, amount)
    await ctx.send(embed=embed_msg("✅ Points Added (MCLINES)", f"{member.mention} now has `{score}` points."))


@bot.command()
async def bulkpointsmc(ctx, amount: int, *members: discord.Member):
    if not ctx.author.guild_permissions.administrator:
        return await ctx.send(embed=embed_msg("❌ No Permission", "Admin only command.", discord.Color.red()))

    if not members:
        return await ctx.send(embed=embed_msg("⚠️ Error", "Mention at least one user.", discord.Color.red()))

    desc = ""
    for member in members:
        score = add_point(member.id, amount)
        desc += f"{member.mention} → `{score}` points\n"

    await ctx.send(embed=embed_msg("✅ Bulk Points Added (MCLINES)", desc))

@bot.command()
async def removepointsmc(ctx, member: discord.Member, amount: int):
    if not ctx.author.guild_permissions.administrator:
        return await ctx.send(embed=embed_msg("❌ No Permission", "Admin only command.", discord.Color.red()))

    c.execute("SELECT score FROM points WHERE user_id = ?", (str(member.id),))
    row = c.fetchone()
    current = row[0] if row else 0
    new_score = max(0, current - amount)

    c.execute("INSERT OR REPLACE INTO points (user_id, score) VALUES (?, ?)", (str(member.id), new_score))
    conn.commit()

    await ctx.send(embed=embed_msg(
        "➖ Points Removed (MCLINES)",
        f"{member.mention} now has `{new_score}` points."
    ))

# ================= GTN =================
import time

gtn_cooldowns = {}
gtn_running = False
gtn_number = None
gtn_channel_id = None
gtn_low = 0
gtn_high = 0


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
        return await ctx.send(embed=embed_msg("❌ Error", "Set GTN channel first.", discord.Color.red()))

    gtn_running = True

    digits = random.choice([3, 4])

    if digits == 3:
        start = random.randint(100, 800)
        end = start + random.randint(200, 400)
    else:
        start = random.randint(1000, 9000)
        end = start + random.randint(200, 500)

    gtn_low = start
    gtn_high = end
    gtn_number = random.randint(gtn_low, gtn_high)

    channel = ctx.guild.get_channel(gtn_channel_id)
    await channel.send(embed=embed_msg(
        "🎯 Guess The Number",
        f"Game started!\nRange: **{gtn_low} — {gtn_high}**"
    ))


@bot.command()
@has_game_role()
async def stopgtn(ctx):
    global gtn_running, gtn_number
    gtn_running = False
    gtn_number = None
    await ctx.send(embed=embed_msg("🛑 Stopped", "GTN stopped.", discord.Color.red()))


@bot.command()
@has_game_role()
async def clearlbgtn(ctx):
    c.execute("DELETE FROM gtn_points")
    conn.commit()
    await ctx.send(embed=embed_msg("🗑️ Cleared", "GTN leaderboard cleared."))


@bot.command()
async def lbgtn(ctx):
    c.execute("SELECT user_id, score FROM gtn_points ORDER BY score DESC LIMIT 10")
    rows = c.fetchall()

    if not rows:
        return await ctx.send(embed=embed_msg("📭 Empty", "GTN leaderboard is empty."))

    desc = ""
    for i, (uid, score) in enumerate(rows, 1):
        desc += f"**{i}.** <@{uid}> → `{score}`\n"

    await ctx.send(embed=embed_msg("🏆 GTN Leaderboard", desc))


@bot.command()
@has_game_role()
async def gtnanswer(ctx):
    if not gtn_running or gtn_number is None:
        return await ctx.send(embed=embed_msg("❌ No Game", "No GTN game is running.", discord.Color.red()))

    await ctx.send(embed=embed_msg("🎯 Current Answer", f"The number is **{gtn_number}**"))


# ================= GTN LISTENER =================
@bot.event
async def on_message(message):

    if message.author.bot:
        return

    global gtn_running, gtn_number

    if gtn_running and message.channel.id == gtn_channel_id and message.content.strip().isdigit():

        now = time.time()
        last = gtn_cooldowns.get(message.author.id, 0)

        if now - last < 2:
            return

        gtn_cooldowns[message.author.id] = now
        guess = int(message.content.strip())

        # correct guess
        if guess == gtn_number:
            score = add_gtn_point(message.author.id)

            await message.channel.send(embed=embed_msg(
                "🎉 Correct Guess!",
                f"{message.author.mention} guessed **{gtn_number}** and now has `{score}` wins!"
            ))

            gtn_running = False
            gtn_number = None
            return

        # hint system
        diff = abs(guess - gtn_number)

        if diff > 100:
            text = "📉 Too Far!"
        elif diff > 70:
            text = "📊 Far!"
        elif diff > 50:
            text = "📈 Close!"
        else:
            text = "🔥 Very Close!"

        hint = "Try higher." if guess < gtn_number else "Try lower."

        await message.channel.send(embed=embed_msg(text, hint))

    await bot.process_commands(message)# ================= ADMIN POINT CONTROL - GTN =================
@bot.command()
async def givepointsgtn(ctx, member: discord.Member, amount: int):
    if not ctx.author.guild_permissions.administrator:
        return await ctx.send(embed=embed_msg("❌ No Permission", "Admin only command.", discord.Color.red()))

    score = add_gtn_point(member.id, amount)
    await ctx.send(embed=embed_msg("✅ Points Added (GTN)", f"{member.mention} now has `{score}` points."))


@bot.command()
async def bulkpointsgtn(ctx, amount: int, *members: discord.Member):
    if not ctx.author.guild_permissions.administrator:
        return await ctx.send(embed=embed_msg("❌ No Permission", "Admin only command.", discord.Color.red()))

    if not members:
        return await ctx.send(embed=embed_msg("⚠️ Error", "Mention at least one user.", discord.Color.red()))

    desc = ""
    for member in members:
        score = add_gtn_point(member.id, amount)
        desc += f"{member.mention} → `{score}` points\n"

    await ctx.send(embed=embed_msg("✅ Bulk Points Added (GTN)", desc))

@bot.command()
async def removepointsgtn(ctx, member: discord.Member, amount: int):
    if not ctx.author.guild_permissions.administrator:
        return await ctx.send(embed=embed_msg("❌ No Permission", "Admin only command.", discord.Color.red()))

    c.execute("SELECT score FROM gtn_points WHERE user_id = ?", (str(member.id),))
    row = c.fetchone()
    current = row[0] if row else 0
    new_score = max(0, current - amount)

    c.execute("INSERT OR REPLACE INTO gtn_points (user_id, score) VALUES (?, ?)", (str(member.id), new_score))
    conn.commit()

    await ctx.send(embed=embed_msg(
        "➖ Points Removed (GTN)",
        f"{member.mention} now has `{new_score}` points."
    ))



# ================= HELP COMMAND =================
@bot.command()
async def help(ctx):

    embed = discord.Embed(title="🎮 NEXUS Game System", color=discord.Color.gold())

    # Admin Section
    if ctx.author.guild_permissions.administrator:
        embed.add_field(
            name="👑 Admin Access Only",
            value="Full administrative permissions.",
            inline=False
        )

        embed.add_field(
            name="⚙️ Admin Point Commands",
            value="""
`*givepointsmc @user amount`
`*bulkpointsmc amount @user1 @user2`
`*removepointsmc @user amount`

`*givepointsgtn @user amount`
`*bulkpointsgtn amount @user1 @user2`
`*removepointsgtn @user amount`
""",
            inline=False
        )

    # Game Manager Section
    if any(role.id == GAME_MANAGER_ROLE_ID for role in ctx.author.roles):
        embed.add_field(
            name="🎮 Game Manager Commands",
            value="""
`*setmclines`
`*startmcline`
`*stopmcline`
`*clearlbmclines`
`*setgtn`
`*srtgtn`
`*stopgtn`
`*clearlbgtn`
`*gtnanswer`
""",
            inline=False
        )

    # Public Section
    embed.add_field(
        name="🌍 Public Commands",
        value="""
`*lbmclines`
`*lbgtn`
`*help`
""",
        inline=False
    )

    embed.set_footer(text="NEXUS Game Command System ✨")
    await ctx.send(embed=embed)



# ================= MESSAGE LISTENER =================
@bot.event
async def on_message(message):
    global game_running, current_answer
    global gtn_running, gtn_number, gtn_low, gtn_high

    if message.author.bot:
        return

    # MCLINES
    if game_running and current_answer:
        c.execute("SELECT value FROM config WHERE key = ?", ("game_channel",))
        row = c.fetchone()
        if row and message.channel.id == int(row[0]):
            norm = lambda t: re.sub(r"[^\w\s]", "", t.lower()).strip()
            if norm(message.content) == norm(current_answer):
                score = add_point(message.author.id)
                await message.channel.send(
                    embed=embed_msg("🎉 Winner!", f"{message.author.mention} earned `{score}` points!")
                )
                game_running = False
                current_answer = None




    await bot.process_commands(message)

bot.run(TOKEN)














