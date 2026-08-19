WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 800  # both divide evenly by TILE_SIZE (40x25 tile viewport)
FPS = 60

TILE_SIZE = 32
GRID_WIDTH = 60
GRID_HEIGHT = 45

VIEWPORT_TILES_X = WINDOW_WIDTH // TILE_SIZE
VIEWPORT_TILES_Y = WINDOW_HEIGHT // TILE_SIZE

CAMERA_PAN_SPEED = 400  # pixels/sec

DAY_SECONDS = 120
NIGHT_SECONDS = 60

START_CLAIM_RADIUS = 5  # buildable tiles around start
START_REVEAL_RADIUS = 8  # fog cleared further out than claimed, giving Expand a frontier to target

COLOR_BG = (18, 18, 24)
COLOR_FOG = (10, 10, 14)
COLOR_TEXT = (230, 230, 230)
COLOR_DAY_BANNER = (255, 214, 100)
COLOR_NIGHT_BANNER = (120, 140, 255)
COLOR_NPC = (220, 220, 60)
COLOR_NPC_SELECTED = (255, 255, 255)
COLOR_HOVER_BORDER = (100, 220, 255)
COLOR_BAR_BG = (40, 40, 50)
COLOR_HUNGER_BAR = (230, 180, 50)


# --- Gather UX polish: queued-task marker, work progress, Expand preview ---
COLOR_QUEUED_WAITING = (255, 200, 90)   # task queued, no NPC assigned yet
COLOR_QUEUED_ASSIGNED = (140, 255, 140)  # an NPC has claimed it and is en route/working
COLOR_PROGRESS_BAR = (120, 200, 255)
COLOR_EXPAND_PREVIEW_CLAIM = (140, 255, 140, 90)  # will newly become claimed/grass - alpha-blended overlay

STARTING_NPC_COUNT = 3
NPC_RADIUS = TILE_SIZE // 3

# --- NPC Stats & Hunger (ticket 08) ---
NPC_MAX_HEALTH = 100
NPC_MAX_HUNGER = 100.0
HUNGER_DECAY_RATE = NPC_MAX_HUNGER / (DAY_SECONDS * 2)   # hunger points lost per second (~0.417, lasts 2 full days without food)
HUNGER_EAT_THRESHOLD = 60.0                              # hunger level at which NPC consumes food from inventory
HUNGER_RESTORE_PER_CROP = 50.0                           # hunger points restored per crop eaten
NPC_ATTACK = 12
NPC_DEFENSE = 4

# --- Combat (ticket 06) ---
MONSTER_SPEED = 60.0  # pixels/sec, slower than NPC_DEFAULT_SPEED
MONSTER_MAX_HEALTH = 40
MONSTER_ATTACK = 10
MONSTER_DEFENSE = 2

COMBAT_RANGE = TILE_SIZE * 1.1  # "adjacent" threshold for auto-engage
COMBAT_MIN_DAMAGE = 1  # damage floor so attack <= defense still chips away

NEST_INITIAL_COUNT = 3
NEST_MAX_COUNT = 8
# At round 1 this yields ~1 spawn/nest over a NIGHT_SECONDS=60 night (3 nests
# -> ~3 monsters) - the old 15.0 gave up to 4/nest (~12 total) on the very
# first night, before the colony has any defenses.
NEST_BASE_SPAWN_INTERVAL = 40.0  # seconds between spawns at round 1
NEST_SPAWN_RAMP_PER_ROUND = 2.5  # interval shrinks by this much per round
NEST_MIN_SPAWN_INTERVAL = 4.0  # floor so late rounds don't spawn every tick
NEW_NEST_INTERVAL = 240.0  # seconds between chances for a new nest to appear

COLOR_MONSTER = (200, 60, 60)
COLOR_NEST = (120, 20, 20)
COLOR_HEALTH_BAR = (200, 60, 60)
COLOR_HUNGER_BAR = (220, 160, 40)
COLOR_BAR_BG = (40, 40, 40)

# --- Gather (ticket 02) ---
GATHER_WORK_SECONDS = 2.0
GATHER_YIELD = 1

# --- Expand (ticket 03) ---
EXPAND_WORK_SECONDS = 3.0
EXPAND_CLAIM_RADIUS = 2
EXPAND_REVEAL_RADIUS = 3

# --- Build (ticket 04) ---
WALL_BLOCK = 100
WALL_ATTACK = 0
WALL_COST = {"wood": 4}
WALL_WORK_SECONDS = 3.0
COLOR_WALL = (140, 140, 140)

TOWER_BLOCK = 10
TOWER_ATTACK = 15
TOWER_COST = {"wood": 2, "bricks": 3}
TOWER_WORK_SECONDS = 5.0
COLOR_TOWER = (100, 120, 160)

# --- Destroy task ---
DESTROY_WORK_SECONDS = 2.0

# --- Building combat integration (ticket 07) ---
TOWER_RANGE = TILE_SIZE * 4  # ranged attack, no adjacency required unlike NPCs

# --- Wave settlement & skill points (ticket 22) ---
WAVE_FULL_CLEAR_POINTS = 2
WAVE_PARTIAL_CLEAR_KILLS_PER_POINT = 5

# --- Game over & scoring (ticket 09) ---
COLOR_GAME_OVER = (255, 90, 90)

# --- Roles (ticket 12) ---
ROLE_FARMER = "Farmer"
ROLE_KNIGHT = "Knight"
ROLE_MAGE = "Mage"
ROLES = (ROLE_FARMER, ROLE_KNIGHT, ROLE_MAGE)

MAGE_COMBAT_RANGE = TILE_SIZE * 3  # ranged, unlike the melee-adjacent default

ROLE_STATS = {
    ROLE_FARMER: {
        "attack": 8, "defense": 3, "max_health": 100,
        "combat_range": COMBAT_RANGE, "work_multiplier": 0.6,
    },
    ROLE_KNIGHT: {
        "attack": 18, "defense": 8, "max_health": 140,
        "combat_range": COMBAT_RANGE, "work_multiplier": 1.0,
    },
    ROLE_MAGE: {
        "attack": 22, "defense": 2, "max_health": 70,
        "combat_range": MAGE_COMBAT_RANGE, "work_multiplier": 1.0,
    },
}

COLOR_ROLE_FARMER = (120, 200, 90)
COLOR_ROLE_KNIGHT = (170, 190, 210)
COLOR_ROLE_MAGE = (160, 90, 220)

# --- Material taxonomy (ticket 14) ---
# None is the "no resource" weight so the whole table sums to 1.0 and a single
# rng.choices() call per tile replaces the old rng.random() < RESOURCE_CHANCE
# roll. crop keeps its original 0.12 weight unchanged - task.py's hunger-eat
# still only consumes crop (generalizing that is ticket 27's job), so
# shrinking crop's share to make room for the new materials would have
# quietly made starvation harder. The new materials are added as genuinely
# new density on top, not carved out of crop's slice. wood/bricks weights are
# sized so their expected tile count within the starting claim area
# (121 tiles at START_CLAIM_RADIUS=5) clears WALL_COST/TOWER_COST with
# comfortable margin (~2x), matching the old design's affordability margin.
RESOURCE_WEIGHTS = {
    None: 0.70,
    "crop": 0.12,
    "wood": 0.07,
    "bricks": 0.05,
    "marble": 0.02,
    "berries": 0.02,
    "raw_stone": 0.02,
}

# --- Magic framework + Lightning (ticket 18) ---
LIGHTNING_DAMAGE = 35
LIGHTNING_COOLDOWN = 20.0
MAGIC_FLASH_DURATION = 0.3
COLOR_LIGHTNING_FLASH = (255, 255, 120)

# --- Fire spell (ticket 19) ---
FIRE_DAMAGE = 25
FIRE_COOLDOWN = 15.0
FIRE_BURN_DAMAGE_PER_TICK = 5
FIRE_BURN_TICKS = 3
FIRE_BURN_TICK_INTERVAL = 1.0
COLOR_FIRE_FLASH = (255, 120, 40)

# --- Freeze spell (ticket 20) ---
FREEZE_COOLDOWN = 25.0
FREEZE_DURATION = 4.0
FREEZE_RADIUS = 1  # 3x3 box: center tile +/- this radius on each axis
COLOR_FREEZE_FLASH = (140, 220, 255)

# --- Monster variety (ticket 21) ---
MONSTER_WEREWOLF = "Werewolf"
MONSTER_VAMPIRE = "Vampire"
MONSTER_ZOMBIE = "Zombie"

MONSTER_STATS = {
    MONSTER_WEREWOLF: {"speed": 80.0, "max_health": 50, "attack": 14, "defense": 2, "life_steal": False},
    MONSTER_VAMPIRE: {"speed": 70.0, "max_health": 40, "attack": 12, "defense": 3, "life_steal": True},
    MONSTER_ZOMBIE: {"speed": 40.0, "max_health": 90, "attack": 8, "defense": 4, "life_steal": False},
}

MONSTER_SPAWN_WEIGHTS = {MONSTER_WEREWOLF: 4, MONSTER_VAMPIRE: 3, MONSTER_ZOMBIE: 3}

# --- House & population cap (ticket 15) ---
BASE_POPULATION_CAP = 3
HOUSE_BLOCK = 0
HOUSE_ATTACK = 0
HOUSE_COST = {"wood": 4, "bricks": 2}
HOUSE_WORK_SECONDS = 4.0
COLOR_HOUSE = (180, 140, 90)
COLOR_UNKNOWN_BUILDING = (255, 0, 255)  # unmistakable "missing render mapping" marker

# --- Farmland (ticket 17) ---
FARMLAND_BLOCK = 0
FARMLAND_ATTACK = 0
FARMLAND_COST = {"wood": 2, "crop": 1}
FARMLAND_WORK_SECONDS = 3.0
FARMLAND_GROW_SECONDS = 20.0
FARMLAND_YIELD = 3
HARVEST_FARMLAND_WORK_SECONDS = 2.0
COLOR_FARMLAND = (100, 160, 60)
COLOR_FARMLAND_READY = (220, 190, 60)

# --- Wildlife / animal fauna (ticket 24) ---
ANIMAL_INITIAL_COUNT = 10
ANIMAL_MAX_COUNT = 20
ANIMAL_SPAWN_INTERVAL = 30.0  # seconds between top-up spawn attempts while under cap

# species -> (speed px/s, dangerous, health)
ANIMAL_SPECIES = {
    "FlyingSquirrel": (100.0, False, 10),
    "Fish": (60.0, False, 10),
    "WildBoar": (70.0, False, 30),
    "Horse": (140.0, False, 40),
    "Wolf": (90.0, True, 35),
    "Bear": (50.0, True, 60),
}

COLOR_ANIMAL = (150, 190, 90)
COLOR_ANIMAL_DANGEROUS = (200, 140, 60)

# --- Hunt Task (ticket 25) ---
HUNT_WORK_SECONDS = 2.0
KNIGHT_CRIT_CHANCE = 0.50
KNIGHT_CRIT_MULTIPLIER = 2.0

# --- Post-Hunt & Taming (ticket 26) ---
ANIMAL_MEAT_YIELD = {
    "FlyingSquirrel": 1,
    "Fish": 1,
    "WildBoar": 3,
    "Horse": 3,
    "Wolf": 2,
    "Bear": 5,
}

BASE_TAME_SUCCESS_RATE = 0.50
FARMER_TAME_SUCCESS_MULTIPLIER = 1.50
TAME_WORK_SECONDS = 3.0
# No FARMER_TAME_WORK_MULTIPLIER: the ticket's "1.5x ... speed vs. other
# roles" is already delivered by the generic per-role work_multiplier
# (task.py applies it to every task type, Tame included) - see tame_task.py's
# module docstring for why a Tame-specific multiplier would double-stack it.

ANIMAL_PEN_WORK_SECONDS = 4.0
ANIMAL_PEN_COST = {"wood": 4, "raw_stone": 2}
ANIMAL_PEN_BLOCK = 20
ANIMAL_PEN_ATTACK = 0
COLOR_ANIMAL_PEN = (160, 130, 90)

PEN_PRODUCTION_INTERVAL = 30.0  # seconds between food production ticks
HORSE_SPEED_BONUS = 30.0  # travel speed buff for colony NPCs when horse is penned

# --- Food Spoilage (ticket 27) ---
DAY_NIGHT_CYCLE_SECONDS = DAY_SECONDS + NIGHT_SECONDS  # 180s per game day
RAW_FOOD_SHELF_LIFE = 3.0 * DAY_NIGHT_CYCLE_SECONDS     # 540s (3 game days)
PROCESSED_FOOD_SHELF_LIFE = 5.0 * DAY_NIGHT_CYCLE_SECONDS  # 900s (5 game days)

FOOD_SHELF_LIFE = {
    "crop": RAW_FOOD_SHELF_LIFE,
    "meat": RAW_FOOD_SHELF_LIFE,
    "mushrooms": RAW_FOOD_SHELF_LIFE,
    "berries": PROCESSED_FOOD_SHELF_LIFE,
}

# --- Skill Upgrade UI & Tree (ticket 23) ---
SKILL_GATHER_SPEED = "Gather Speed"
SKILL_HUNTING_ACCURACY = "Hunting Accuracy"
SKILL_TAMING_ABILITY = "Taming Ability"
SKILL_DEFENSE_ABILITY = "Defense Ability"
SKILL_MAGIC_ATTACK = "Magic Attack"
SKILL_AOE_ATTACK = "AoE Attack"
SKILL_NAMES = (
    SKILL_GATHER_SPEED, SKILL_HUNTING_ACCURACY, SKILL_TAMING_ABILITY,
    SKILL_DEFENSE_ABILITY, SKILL_MAGIC_ATTACK, SKILL_AOE_ATTACK,
)

GATHER_SPEED_REDUCTION_PER_LEVEL = 0.10  # 10% less Gather work-seconds/level, stacks with role multiplier
HUNTING_ACCURACY_CRIT_BONUS_PER_LEVEL = 0.10  # +10pp Knight crit chance vs fauna, per level
TAMING_SUCCESS_BONUS_PER_LEVEL = 0.10  # +10pp tame success rate, per level
DEFENSE_BONUS_PER_LEVEL = 2  # flat defense, on top of role-based base
HEALTH_BONUS_PER_LEVEL = 10  # flat max_health (and current health), on top of role-based base
MAGIC_DAMAGE_MULTIPLIER_PER_LEVEL = 0.15  # +15% spell damage, per level
AOE_RADIUS_BONUS_PER_LEVEL = 1  # +1 tile to Freeze's 3x3 box radius, per level

# --- NPC Drag-to-Heal Sanctuary System ---
SANCTUARY_HEAL_RATE = 2.5  # Balanced HP restored per second while in Sanctuary (takes ~30-45s for full recovery)

