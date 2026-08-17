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

STARTING_NPC_COUNT = 3
NPC_RADIUS = TILE_SIZE // 3

# --- Combat (ticket 06) ---
NPC_MAX_HEALTH = 100
NPC_ATTACK = 12
NPC_DEFENSE = 4

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

# --- Gather (ticket 02) ---
GATHER_WORK_SECONDS = 2.0
GATHER_YIELD = 1

# --- Build (ticket 04) ---
WALL_BLOCK = 100
WALL_ATTACK = 0
WALL_COST = {"crop": 2}
WALL_WORK_SECONDS = 3.0
COLOR_WALL = (140, 140, 140)

TOWER_BLOCK = 10
TOWER_ATTACK = 15
TOWER_COST = {"crop": 5}
TOWER_WORK_SECONDS = 5.0
COLOR_TOWER = (100, 120, 160)

