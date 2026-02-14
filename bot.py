import os
import discord
from discord.ext import commands
import random
import sqlite3
import re

# ================= CONFIG =================
TOKEN = os.getenv("DISCORD_TOKEN")
GAME_MANAGER_ROLE_ID = 1468173295760314473
OWNER_ID = 1448709644091527363
DB_FILE = "bot_data.db"

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix="*", intents=intents, help_command=None)

# ================= DATA & STATE =================
GAMES_DATA = {
    "mc": {"name": "Minecraft Lines", "table": "mc_points", "color": discord.Color.green()},
    "gtn": {"name": "Guess The Number", "table": "gtn_points", "color": discord.Color.blue()},
    "quiz": {"name": "MC Quiz", "table": "quiz_points", "color": discord.Color.purple()}
}

game_state = {
    "mc": {"active": False, "answer": None},
    "gtn": {"active": False, "number": None},
    "quiz": {"active": False, "question": None, "answer": None}
}

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
    ("Which mob attacks in packs?", "wolf")
]

# ================= DATABASE =================
conn = sqlite3.connect(DB_FILE, check_same_thread=False)
c = conn.cursor()
for key in GAMES_DATA:
    c.execute(f"CREATE TABLE IF NOT EXISTS {GAMES_DATA[key]['table']}(user_id INTEGER PRIMARY KEY, score INTEGER DEFAULT 0)")
c.execute("CREATE TABLE IF NOT EXISTS config(key TEXT PRIMARY KEY, value TEXT)")
conn.commit()

# ================= UTILS =================
def is_auth(ctx_or_inter):
    user = ctx_or_inter.author if hasattr(ctx_or_inter, 'author') else ctx_or_inter.user
    return user.guild_permissions.administrator or any(r.id == GAME_MANAGER_ROLE_ID for r in user.roles) or user.id == OWNER_ID

def update_db_points(table, user_id, amount):
    c.execute(f"INSERT OR IGNORE INTO {table}(user_id) VALUES(?)", (user_id,))
    c.
