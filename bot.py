import discord
from discord.ext import commands
from datetime import datetime, timezone
import random
import sqlite3

# ================= CONFIG =================
TOKEN = "PUT_YOUR_BOT_TOKEN_HERE"

VERIFIED_ROLE_ID = 1467128845093175397
NON_VERIFIED_ROLE_ID = 1467128749987336386

MIN_ACCOUNT_AGE_DAYS = 20
DB_FILE = "bot_data.db"
# =========================================

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="*", intents=intents)

# ================= DATABASE =================
conn = sqlite3.connect(DB_FILE)
c = conn.cursor()

# Create tables if they don't exist
c.execute("""CREATE TABLE IF NOT EXISTS points (
                user_id TEXT PRIMARY KEY,
                score INTEGER
            )""")
c.execute("""CREATE TABLE IF NOT EXISTS config (
                key TEXT PRIMARY KEY,
                value TEXT
            )""")
conn.commit()

def get_points(user_id):
    c.execute("SELECT score FROM points WHERE user_id = ?", (str(user_id),))
    row = c.fetchone()
    return row[0] if row else 0

def add_point(user_id):
    score = get_points(user_id) + 1
    c.execute("INSERT OR REPLACE INTO points (user_id, score) VALUES (?, ?)", (str(user_id), score))
    conn.commit()
    return score

def clear_points():
    c.execute("DELETE FROM points")
    conn.commit()

def save_config(key, value):
    c.execute("INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)", (key, str(value)))
    conn.commit()

def load_config(key):
    c.execute("SELECT value FROM config WHERE key = ?", (key,))
    row = c.fetchone()
    return int(row[0]) if row else None

# ================= VERIFICATION DATA =================
verify_channel_id = load_config("verify_channel")
captcha_answers = {}

# ================= GAME DATA =================
sentences = [
     "creeper aw man",
    "never dig straight down",
    "minecraft is a sandbox game",
    "diamond armor is very rare",
    "the ender dragon lives in the end",
    "villagers trade emeralds",
    "nether portals need obsidian"
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

game_running = False
current_answer = None

def scramble_and_invert(sentence):
    words = sentence.split()
    random.shuffle(words)
    return " ".join(word[::-1] for word in words)

# ================= READY =================
@bot.event
async def on_ready():
    print(f"✅ Bot online as {bot.user}")

# ================= MEMBER JOIN =================
@bot.event
async def on_member_join(member):
    account_age = (datetime.now(timezone.utc) - member.created_at).days

    if account_age < MIN_ACCOUNT_AGE_DAYS:
        await member.ban(reason="Account too new (anti-alt)")
        return

    role = member.guild.get_role(NON_VERIFIED_ROLE_ID)
    if role:
        await member.add_roles(role)

    if verify_channel_id:
        channel = member.guild.get_channel(verify_channel_id)
        if channel:
            await channel.send(
                f"{member.mention} click below to verify 👇",
                view=VerifyView(member.id)
            )

# ================= VERIFY UI =================
class VerifyView(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=300)
        self.user_id = user_id

    @discord.ui.button(label="Verify", style=discord.ButtonStyle.success)
    async def verify(self, interaction: discord.Interaction, _):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ Not for you.", ephemeral=True)
            return

        a, b = random.randint(1, 10), random.randint(1, 10)
        captcha_answers[interaction.user.id] = str(a + b)
        await interaction.response.send_modal(CaptchaModal(a, b))

class CaptchaModal(discord.ui.Modal, title="Verification CAPTCHA"):
    def __init__(self, a, b):
        super().__init__()
        self.answer = discord.ui.TextInput(label=f"{a} + {b} = ?", required=True)
        self.add_item(self.answer)

    async def on_submit(self, interaction: discord.Interaction):
        if self.answer.value.strip() == captcha_answers.get(interaction.user.id):
            await interaction.user.add_roles(
                interaction.guild.get_role(VERIFIED_ROLE_ID)
            )
            await interaction.user.remove_roles(
                interaction.guild.get_role(NON_VERIFIED_ROLE_ID)
            )
            await interaction.response.send_message("✅ Verified!", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Wrong answer.", ephemeral=True)

# ================= VERIFICATION COMMANDS =================
@bot.command()
@commands.has_permissions(administrator=True)
async def setverifychannel(ctx, channel: discord.TextChannel):
    global verify_channel_id
    verify_channel_id = channel.id
    save_config("verify_channel", verify_channel_id)
    await ctx.send(f"✅ Verification channel set to {channel.mention}")

@bot.command()
@commands.has_permissions(manage_roles=True)
async def verify(ctx, member: discord.Member):
    await member.add_roles(ctx.guild.get_role(VERIFIED_ROLE_ID))
    await member.remove_roles(ctx.guild.get_role(NON_VERIFIED_ROLE_ID))
    await ctx.send(f"✅ {member.mention} verified.")

@bot.command()
@commands.has_permissions(manage_roles=True)
async def unverify(ctx, member: discord.Member):
    await member.remove_roles(ctx.guild.get_role(VERIFIED_ROLE_ID))
    await member.add_roles(ctx.guild.get_role(NON_VERIFIED_ROLE_ID))
    await ctx.send(f"⚠️ {member.mention} unverified.")

# ================= CHAT GAME =================
@bot.command()
async def startgame(ctx):
    global game_running, current_answer
    if game_running:
        return await ctx.send("⚠️ Game already running.")

    sentence = random.choice(sentences)
    current_answer = sentence.lower()
    game_running = True

    await ctx.send(f"🎮 **CHAT GAME**\n🧩 `{scramble_and_invert(sentence)}`")

@bot.event
async def on_message(message):
    global game_running, current_answer

    if message.author.bot:
        return

    if game_running and message.content.lower() == current_answer:
        game_running = False
        score = add_point(message.author.id)

        await message.channel.send(
            f"🏆 {message.author.mention} WON!\n⭐ Points: {score}"
        )
        current_answer = None

    await bot.process_commands(message)

@bot.command()
async def leaderboard(ctx):
    c.execute("SELECT user_id, score FROM points ORDER BY score DESC LIMIT 10")
    rows = c.fetchall()
    if not rows:
        return await ctx.send("❌ No scores yet.")

    text = "🏆 **LEADERBOARD**\n"
    for i, (uid, score) in enumerate(rows, 1):
        try:
            user = await bot.fetch_user(int(uid))
            text += f"{i}. {user.name} — {score}\n"
        except:
            pass
    await ctx.send(text)

@bot.command()
@commands.has_permissions(administrator=True)
async def clearleaderboard(ctx):
    clear_points()
    await ctx.send("🗑️ Leaderboard cleared.")

@bot.command()
async def stop(ctx):
    global game_running, current_answer
    game_running = False
    current_answer = None
    await ctx.send("🛑 Game stopped.")

# ================= RUN =================
bot.run(TOKEN)







