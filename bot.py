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
# ---------------- STOP GAME ----------------
@bot.command()
async def stop(ctx):
    global game_running, current_answer

    if not game_running:
        await ctx.send("❌ There is no game running right now.")
        return

    game_running = False
    current_answer = None

    await ctx.send("🛑 **The game has been stopped.**")

# ---------------- RUN BOT ----------------
bot.run(os.getenv("DISCORD_TOKEN"))






