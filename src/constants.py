WINDOW_WIDTH = 1024
WINDOW_HEIGHT = 768
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
COLOR_UNCLAIMED = (60, 60, 68)
COLOR_CLAIMED_EMPTY = (72, 96, 60)
COLOR_RESOURCE = (196, 168, 60)
COLOR_GRID_LINE = (0, 0, 0)
COLOR_TEXT = (230, 230, 230)
COLOR_DAY_BANNER = (255, 214, 100)
COLOR_NIGHT_BANNER = (120, 140, 255)
COLOR_NPC = (220, 220, 60)
COLOR_NPC_SELECTED = (255, 255, 255)
COLOR_HOVER_BORDER = (100, 220, 255)

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
NEST_BASE_SPAWN_INTERVAL = 15.0  # seconds between spawns at round 1
NEST_SPAWN_RAMP_PER_ROUND = 1.0  # interval shrinks by this much per round
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

# --- Game over & scoring (ticket 09) ---
COLOR_GAME_OVER = (255, 90, 90)

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
