import os
import discord
from discord.ext import commands
import random
import sqlite3
import re
import string

# ================= CONFIG =================
TOKEN = os.getenv("DISCORD_TOKEN")

VERIFIED_ROLE_ID = 1467128845093175397
NON_VERIFIED_ROLE_ID = 1467128749987336386
GAME_MANAGER_ROLE_ID = 1468173295760314473

DB_FILE = "bot_data.db"
# =========================================

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="*", intents=intents, help_command=None)

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

# ================= REVERSE FUNCTION =================
def reverse_sentence(sentence):
    return sentence[::-1]

# ================= ROLE CHECK =================
def has_game_role():
    async def predicate(ctx):
        return any(role.id == GAME_MANAGER_ROLE_ID for role in ctx.author.roles)
    return commands.check(predicate)

# ================= DATABASE SETUP =================
conn = sqlite3.connect(DB_FILE, check_same_thread=False)
c = conn.cursor()
c.execute("CREATE TABLE IF NOT EXISTS points (user_id TEXT PRIMARY KEY, score INTEGER)")
c.execute("CREATE TABLE IF NOT EXISTS config (key TEXT PRIMARY KEY, value TEXT)")
conn.commit()

def add_point(user_id):
    c.execute("SELECT score FROM points WHERE user_id = ?", (str(user_id),))
    row = c.fetchone()
    score = (row[0] if row else 0) + 1
    c.execute("INSERT OR REPLACE INTO points (user_id, score) VALUES (?, ?)", (str(user_id), score))
    conn.commit()
    return score

# ================= AUTO-ROLE ON JOIN =================
@bot.event
async def on_member_join(member):
    role = member.guild.get_role(NON_VERIFIED_ROLE_ID)
    if role:
        try:
            await member.add_roles(role)
        except Exception as e:
            print(f"Error giving role: {e}")


# ================= ADMIN POINT COMMANDS =================
@bot.command()
@commands.has_permissions(administrator=True)
async def clearlb(ctx):
    c.execute("DELETE FROM points")
    conn.commit()
    await ctx.send("🗑️ **Leaderboard has been cleared!** All points are back to 0.")

@bot.command()
@commands.has_permissions(administrator=True)
async def setpoints(ctx, member: discord.Member, amount: int):
    c.execute("INSERT OR REPLACE INTO points (user_id, score) VALUES (?, ?)", (str(member.id), amount))
    conn.commit()
    await ctx.send(f"🎯 Set {member.mention}'s points to `{amount}`.")

@bot.command()
@commands.has_permissions(administrator=True)
async def givepoints(ctx, member: discord.Member, amount: int):
    c.execute("SELECT score FROM points WHERE user_id = ?", (str(member.id),))
    row = c.fetchone()
    current = row[0] if row else 0
    new_total = current + amount
    c.execute("INSERT OR REPLACE INTO points (user_id, score) VALUES (?, ?)", (str(member.id), new_total))
    conn.commit()
    await ctx.send(f"✅ Added `{amount}` points to {member.mention}. New total: `{new_total}`.")

# ================= GAME COMMANDS =================
@bot.command()
@has_game_role()
async def setgamechannel(ctx, channel: discord.TextChannel):
    c.execute("INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)", ("game_channel", str(channel.id)))
    conn.commit()
    await ctx.send(f"✅ Game channel set to: {channel.mention}")

@bot.command()
@has_game_role()
async def startgame(ctx):
    global game_running, current_answer
    if game_running: return await ctx.send("⚠️ Game already running.")

    c.execute("SELECT value FROM config WHERE key = ?", ("game_channel",))
    row = c.fetchone()
    if not row: return await ctx.send("❌ Use `*setgamechannel` first.")

    channel = ctx.guild.get_channel(int(row[0]))
    game_running = True
    current_answer = random.choice(sentences)
    await channel.send(f"🎮 **New Game!** Reverse this sentence:\n`{reverse_sentence(current_answer)}`")

@bot.command()
@has_game_role()
async def stopgame(ctx):
    global game_running, current_answer
    game_running, current_answer = False, None
    await ctx.send("🛑 Game stopped.")

@bot.command()
async def lb(ctx):
    c.execute("SELECT user_id, score FROM points ORDER BY score DESC LIMIT 10")
    rows = c.fetchall()
    if not rows: return await ctx.send("📭 Empty leaderboard.")
    msg = "**🏆 TOP 10 LEADERBOARD**\n\n"
    for i, (u_id, score) in enumerate(rows, 1):
        msg += f"**{i}.** <@{u_id}> → `{score}`\n"
    await ctx.send(msg)
@bot.command()
async def help(ctx):
    msg = (
        "**🤖 BOT COMMAND HELP**\n\n"
        "**👑 Admin Commands**\n"
        "`*givepoints @user amount` → Add points to a user\n\n"
        "**🎮 Game Manager Commands**\n"
        "`*setgamechannel #channel` → Set game channel\n"
        "`*startgame` → Start the game\n"
        "`*stopgame` → Stop the game\n"
        "`*clearlb` → Clear leaderboard (if added)\n\n"
        "**👤 Public Commands**\n"
        "`*lb` → Show leaderboard\n"
    )
    await ctx.send(msg)



# ================= MESSAGE LISTENER =================
@bot.event
async def on_message(message):
    global game_running, current_answer
    if message.author.bot: return

    if game_running and current_answer:
        c.execute("SELECT value FROM config WHERE key = ?", ("game_channel",))
        row = c.fetchone()
        if row and message.channel.id == int(row[0]):
            norm = lambda t: re.sub(r"[^\w\s]", "", t.lower()).strip()
            if norm(message.content) == norm(current_answer):
                score = add_point(message.author.id)
                await message.channel.send(f"🎉 {message.author.mention} got it! Total: {score}")
                game_running, current_answer = False, None

    await bot.process_commands(message)

bot.run(TOKEN)




