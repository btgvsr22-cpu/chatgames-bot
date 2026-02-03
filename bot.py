import os
import discord
from discord.ext import commands
from datetime import datetime, timezone
import random
import sqlite3
import re
import string

# ================= CONFIG =================
TOKEN = os.getenv("DISCORD_TOKEN")

VERIFIED_ROLE_ID = 1467128845093175397
NON_VERIFIED_ROLE_ID = 1467128749987336386

GAME_MANAGER_ROLE_ID = 1468173295760314473

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

# ================= SENTENCES (UPDATED) =================
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

# ================= SCRAMBLE + INVERT FUNCTION =================
def scramble_and_invert(sentence):
    words = sentence.split()
    scrambled_words = []

    for word in words:
        if len(word) > 1:
            letters = list(word)
            random.shuffle(letters)
            scrambled_words.append("".join(letters))
        else:
            scrambled_words.append(word)

    return " ".join(scrambled_words[::-1])

# ================= ROLE CHECK =================
def has_game_role():
    async def predicate(ctx):
        return any(role.id == GAME_MANAGER_ROLE_ID for role in ctx.author.roles)
    return commands.check(predicate)

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

# ================= GAME CONTROL =================
@bot.command()
@has_game_role()
async def stop(ctx):
    global game_running, current_answer
    game_running = False
    current_answer = None
    await ctx.send("🛑 Game stopped.")

# ================= POINT COMMANDS (ADMIN) =================
@bot.command()
@commands.has_permissions(administrator=True)
async def givepoints(ctx, member: discord.Member, amount: int):
    new_score = get_points(member.id) + amount
    c.execute(
        "INSERT OR REPLACE INTO points (user_id, score) VALUES (?, ?)",
        (str(member.id), new_score)
    )
    safe_commit()
    await ctx.send(f"✅ Added {amount} points to {member.mention}. New total: {new_score}")

@bot.command()
@commands.has_permissions(administrator=True)
async def removepoints(ctx, member: discord.Member, amount: int):
    new_score = max(0, get_points(member.id) - amount)
    c.execute(
        "INSERT OR REPLACE INTO points (user_id, score) VALUES (?, ?)",
        (str(member.id), new_score)
    )
    safe_commit()
    await ctx.send(f"📉 Removed {amount} points from {member.mention}. New total: {new_score}")

@bot.command()
@commands.has_permissions(administrator=True)
async def setpoints(ctx, member: discord.Member, amount: int):
    c.execute(
        "INSERT OR REPLACE INTO points (user_id, score) VALUES (?, ?)",
        (str(member.id), amount)
    )
    safe_commit()
    await ctx.send(f"🎯 Set {member.mention}'s points to {amount}")

# ================= LEADERBOARD (PUBLIC) =================
@bot.command(name="lb")
async def leaderboard(ctx):
    c.execute("SELECT user_id, score FROM points ORDER BY score DESC LIMIT 10")
    rows = c.fetchall()

    if not rows:
        await ctx.send("📭 Leaderboard is empty.")
        return

    msg = "**🏆 LEADERBOARD (Top 10)**\n\n"
    for i, (user_id, score) in enumerate(rows, start=1):
        member = ctx.guild.get_member(int(user_id))
        name = member.mention if member else f"<@{user_id}>"
        msg += f"**{i}.** {name} → `{score}` points\n"

    await ctx.send(msg)

# ================= GAME CHANNEL + VERIFICATION COMMANDS =================
@bot.command()
@has_game_role()
async def setgamechannel(ctx, channel: discord.TextChannel):
    c.execute("INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)", ("game_channel", str(channel.id)))
    safe_commit()
    await ctx.send(f"✅ Game channel set to {channel.mention}")

@bot.command()
@commands.has_permissions(administrator=True)
async def setverifychannel(ctx, channel: discord.TextChannel):
    c.execute("INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)", ("verify_channel", str(channel.id)))
    safe_commit()
    await ctx.send(f"✅ Verification channel set to {channel.mention}")

    class VerifyButton(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=None)

        @discord.ui.button(label="Verify", style=discord.ButtonStyle.green)
        async def verify(self, interaction: discord.Interaction, button: discord.ui.Button):
            captcha_text = "".join(random.choices(string.ascii_letters + string.digits, k=5))

            class CaptchaModal(discord.ui.Modal):
                def __init__(self):
                    super().__init__(title="Complete Captcha")
                    self.captcha_input = discord.ui.TextInput(
                        label=f"Type the captcha: {captcha_text}",
                        placeholder="Enter exactly as shown",
                        max_length=10
                    )
                    self.add_item(self.captcha_input)

                async def on_submit(self, modal_interaction: discord.Interaction):
                    member = modal_interaction.user
                    guild = modal_interaction.guild
                    verified_role = guild.get_role(VERIFIED_ROLE_ID)
                    non_verified_role = guild.get_role(NON_VERIFIED_ROLE_ID)

                    if self.captcha_input.value.strip() == captcha_text:
                        if verified_role:
                            await member.add_roles(verified_role)
                        if non_verified_role:
                            await member.remove_roles(non_verified_role)
                        await modal_interaction.response.send_message("✅ Verified successfully!", ephemeral=True)
                    else:
                        await modal_interaction.response.send_message("❌ Incorrect captcha. Try again.", ephemeral=True)

            await interaction.response.send_modal(CaptchaModal())

    await channel.send("🔒 Click the button below to verify yourself!", view=VerifyButton())

# ================= GAME START/STOP (Game Manager only) =================
@bot.command()
@has_game_role()
async def startgame(ctx):
    global game_running, current_answer
    if game_running:
        await ctx.send("⚠️ A game is already running.")
        return

    c.execute("SELECT value FROM config WHERE key = ?", ("game_channel",))
    row = c.fetchone()
    if not row:
        await ctx.send("❌ Game channel not set. Use `*setgamechannel #channel` first.")
        return

    channel_id = int(row[0])
    channel = ctx.guild.get_channel(channel_id)
    if not channel:
        await ctx.send("❌ The configured game channel is invalid.")
        return

    game_running = True
    current_answer = random.choice(sentences)
    scrambled = scramble_and_invert(current_answer)
    await channel.send(f"🎮 **New Game Started!**\nUnscramble this sentence:\n`{scrambled}`")

@bot.command()
@has_game_role()
async def stopgame(ctx):
    global game_running, current_answer
    if not game_running:
        await ctx.send("⚠️ No game is currently running.")
        return
    game_running = False
    current_answer = None
    await ctx.send("🛑 Game stopped.")

# ================= HELP (Game Manager only) =================
@bot.command()
@has_game_role()
async def help(ctx):
    await ctx.send(
        "**📖 BOT COMMANDS (Game Manager Only)**\n\n"
        "**🎮 Chat Game**\n"
        "`*startgame` → Start a new chat game\n"
        "`*stopgame` → Stop the current chat game\n\n"
        "**🏆 Leaderboard**\n"
        "`*lb` → View top 10 leaderboard\n\n"
        "🔒 Access restricted to Game Manager role"
    )

# ================= GAME MESSAGE LISTENER WITH POINTS =================
@bot.event
async def on_message(message):
    global game_running, current_answer

    if message.author.bot:
        return

    if game_running and current_answer:
        c.execute("SELECT value FROM config WHERE key = ?", ("game_channel",))
        row = c.fetchone()
        if row:
            game_channel_id = int(row[0])
            if message.channel.id == game_channel_id:

                def normalize(text):
                    text = text.lower()
                    text = re.sub(r"[^\w\s]", "", text)
                    text = re.sub(r"\s+", " ", text).strip()
                    return text

                if normalize(message.content) == normalize(current_answer):
                    new_score = add_point(message.author.id)
                    await message.channel.send(
                        f"🎉 {message.author.mention} guessed it correctly and earned 1 point! Total: {new_score}"
                    )
                    game_running = False
                    current_answer = None
                    return

    await bot.process_commands(message)

# ================= ERROR HANDLER =================
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send("❌ You don't have permission to use this command.")
        return
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
