import os
import discord
from discord.ext import commands
import random
import json

# ---------------- BOT SETUP ----------------
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="*", intents=intents)

# ---------------- GAME DATA ----------------
sentences = [
    "creeper aw man",
    "never dig straight down",
    "minecraft is a sandbox game",
    "diamond armor is very rare",
    "the ender dragon lives in the end",
    "villagers trade emeralds",
    "nether portals need obsidian"
]

game_running = False
current_answer = None
points_file = "points.json"

# ---------------- POINTS SYSTEM ----------------
def load_points():
    try:
        with open(points_file, "r") as f:
            return json.load(f)
    except:
        return {}

def save_points(points):
    with open(points_file, "w") as f:
        json.dump(points, f, indent=4)

# ---------------- SCRAMBLE + INVERT ----------------
def scramble_and_invert(sentence):
    words = sentence.split()
    random.shuffle(words)              # scramble word order
    inverted = [word[::-1] for word in words]  # invert each word
    return " ".join(inverted)

# ---------------- READY ----------------
@bot.event
async def on_ready():
    print(f"✅ Bot online as {bot.user}")

# ---------------- START GAME (MANUAL) ----------------
@bot.command()
async def startgame(ctx):
    global game_running, current_answer

    if game_running:
        await ctx.send("⚠️ A game is already running!")
        return

    sentence = random.choice(sentences)
    scrambled = scramble_and_invert(sentence)

    current_answer = sentence.lower()
    game_running = True

    await ctx.send(
        f"🎮 **MINECRAFT CHAT GAME**\n"
        f"Unscramble AND fix the inverted words:\n\n"
        f"🧩 `{scrambled}`"
    )

# ---------------- MESSAGE CHECK ----------------
@bot.event
async def on_message(message):
    global game_running, current_answer

    if message.author.bot:
        return

    if game_running and message.content.lower() == current_answer:
        game_running = False

        points = load_points()
        uid = str(message.author.id)
        points[uid] = points.get(uid, 0) + 1
        save_points(points)

        await message.channel.send(
            f"🏆 **{message.author.mention} WON!**\n"
            f"✅ Correct sentence:\n`{current_answer}`\n"
            f"⭐ Points: {points[uid]}"
        )

        current_answer = None

    await bot.process_commands(message)

# ---------------- LEADERBOARD ----------------
@bot.command()
async def leaderboard(ctx):
    points = load_points()

    if not points:
        await ctx.send("❌ Leaderboard is empty.")
        return

    sorted_points = sorted(points.items(), key=lambda x: x[1], reverse=True)

    text = "🏆 **LEADERBOARD** 🏆\n"
    for i, (uid, score) in enumerate(sorted_points[:10], start=1):
        try:
            user = await bot.fetch_user(int(uid))
            text += f"{i}. {user.name} — {score} points\n"
        except:
            pass

    await ctx.send(text)

# ---------------- CLEAR LEADERBOARD ----------------
@bot.command()
@commands.has_permissions(administrator=True)
async def clearleaderboard(ctx):
    save_points({})
    await ctx.send("🗑️ Leaderboard has been cleared.")

# ---------------- RUN BOT ----------------
bot.run(os.getenv("DISCORD_TOKEN"))


