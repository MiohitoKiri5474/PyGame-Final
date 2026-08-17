"""Pygame-free checkpoint save/load. Serializes the full simulation state
(grid, inventory, tasks, buildings, NPCs, nests, monsters, cycle, game-over)
to JSON so the game can resume across sessions/machines from a save file."""

import json
from pathlib import Path

from build_task import Building
from day_night import DayNightCycle
from game_over import GameOverState
from grid import Grid, Tile
from inventory import Inventory
from monster import Monster
from nest import Nest, NestManager
from npc import NPC
from task import Task, TaskQueue
from world import World

SAVE_PATH = Path(__file__).resolve().parent.parent / "save.json"

Checkpoint = tuple[World, DayNightCycle, NestManager, list[Monster], GameOverState, int, int]


def save_checkpoint(
    world: World,
    cycle: DayNightCycle,
    nest_manager: NestManager,
    monsters: list[Monster],
    game_over_state: GameOverState,
    skill_points_available: int = 0,
    monsters_killed_this_night: int = 0,
    path: Path = SAVE_PATH,
) -> None:
    data = dump_state(
        world, cycle, nest_manager, monsters, game_over_state,
        skill_points_available, monsters_killed_this_night,
    )
    Path(path).write_text(json.dumps(data, indent=2))


def dump_state(
    world: World,
    cycle: DayNightCycle,
    nest_manager: NestManager,
    monsters: list[Monster],
    game_over_state: GameOverState,
    skill_points_available: int = 0,
    monsters_killed_this_night: int = 0,
) -> dict:
    """Build the plain-dict serialization of a full simulation state. Exposed
    separately from save_checkpoint so a save->load round trip can be
    verified by comparing two dumps instead of two live object graphs."""
    return {
        "round_number": cycle.round_number,
        "phase": cycle.phase,
        "phase_timer": cycle.timer,
        "game_over": {"is_over": game_over_state.is_over, "score": game_over_state.score},
        "skill_points_available": skill_points_available,
        "monsters_killed_this_night": monsters_killed_this_night,
        "spell_cooldowns": dict(world.spellbook.cooldowns) if hasattr(world, "spellbook") else {},
        "grid": _dump_grid(world.grid),
        "inventory": world.inventory.items(),
        "buildings": [
            {"type": b.type, "x": b.x, "y": b.y, "block": b.block, "attack": b.attack}
            for b in world.buildings
        ],
        "tasks": [
            {
                "type": t.type,
                "target": list(t.target),
                "assigned_npc_id": t.assigned_npc.id if t.assigned_npc else None,
            }
            for t in world.tasks.tasks
        ],
        "npcs": [
            {
                "id": npc.id,
                "x": npc.x,
                "y": npc.y,
                "speed": npc.speed,
                "path": [list(p) for p in npc.path],
                "health": npc.health,
                "hunger": npc.hunger,
                "alive": npc.alive,
                "attack": npc.attack,
                "defense": npc.defense,
                "priority": npc.priority,
                "task_progress": npc.task_progress,
                "role": npc.role,
            }
            for npc in world.npcs
        ],
        "nests": {
            "new_nest_timer": nest_manager.new_nest_timer,
            "nests": [{"x": n.x, "y": n.y, "spawn_timer": n.spawn_timer} for n in nest_manager.nests],
        },
        "monsters": [
            {
                "x": m.x,
                "y": m.y,
                "speed": m.speed,
                "type": m.type,
                "path": [list(p) for p in m.path],
                "health": m.health,
                "attack": m.attack,
                "defense": m.defense,
                "burn_remaining": m.burn_remaining,
                "burn_dps": m.burn_dps,
                "frozen_timer": m.frozen_timer,
            }
            for m in monsters
        ],
    }


def load_checkpoint(path: Path = SAVE_PATH) -> Checkpoint | None:
    """Returns (world, cycle, nest_manager, monsters, game_over_state,
    skill_points_available, monsters_killed_this_night), or None if no
    checkpoint file exists or the file is missing/corrupt (e.g. truncated by
    a crash mid-write) - falls back to a fresh game either way."""
    path = Path(path)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return None

    # ponytail: __new__ bypass mirrors only the fields World/Grid.__init__
    # currently set; a new field added to either constructor needs a matching
    # line here or loaded instances silently miss it. Upgrade when that bites:
    # dataclass-ify World/Grid, or asdict()-style introspection in dump/load.
    world = World.__new__(World)
    world.grid = _load_grid(data["grid"])
    world.inventory = Inventory()
    for resource, amount in data["inventory"].items():
        world.inventory.add(resource, amount)
    world.buildings = [
        Building(type=b["type"], x=b["x"], y=b["y"], block=b["block"], attack=b["attack"])
        for b in data["buildings"]
    ]

    from magic import Spellbook
    world.spellbook = Spellbook()
    world.spellbook.cooldowns = data.get("spell_cooldowns", {})

    tasks = [Task(type=t["type"], target=tuple(t["target"])) for t in data["tasks"]]
    world.tasks = TaskQueue()
    world.tasks.tasks = tasks

    npcs = []
    max_id = -1
    for nd in data["npcs"]:
        npc = NPC(nd["x"], nd["y"], speed=nd["speed"], priority=nd["priority"], role=nd.get("role"))
        npc.id = nd["id"]
        max_id = max(max_id, npc.id)
        npc.path = [tuple(p) for p in nd["path"]]
        npc.health = nd["health"]
        npc.hunger = nd["hunger"]
        npc.alive = nd["alive"]
        npc.attack = nd["attack"]
        npc.defense = nd["defense"]
        npc.task_progress = nd["task_progress"]
        npc.task = None
        npcs.append(npc)
    world.npcs = npcs
    NPC._next_id = max(NPC._next_id, max_id + 1)

    by_id = {npc.id: npc for npc in npcs}
    for task, t in zip(tasks, data["tasks"]):
        npc = by_id.get(t["assigned_npc_id"])
        if npc is not None:
            task.assigned_npc = npc
            npc.task = task

    cycle = DayNightCycle()
    cycle.round_number = data["round_number"]
    cycle.phase = data["phase"]
    cycle.timer = data["phase_timer"]

    game_over_state = GameOverState()
    game_over_state.is_over = data["game_over"]["is_over"]
    game_over_state.score = data["game_over"]["score"]

    nest_manager = NestManager(world.grid.width, world.grid.height)
    nest_manager.new_nest_timer = data["nests"]["new_nest_timer"]
    nest_manager.nests = []
    for nd in data["nests"]["nests"]:
        nest = Nest(nd["x"], nd["y"])
        nest.spawn_timer = nd["spawn_timer"]
        nest_manager.nests.append(nest)

    monsters = []
    for md in data["monsters"]:
        monster = Monster(md["x"], md["y"], speed=md["speed"], type=md.get("type"))
        monster.path = [tuple(p) for p in md["path"]]
        monster.health = md["health"]
        monster.attack = md["attack"]
        monster.defense = md["defense"]
        monster.burn_remaining = md.get("burn_remaining", 0.0)
        monster.burn_dps = md.get("burn_dps", 0.0)
        monster.frozen_timer = md.get("frozen_timer", 0.0)
        monsters.append(monster)


    return (
        world,
        cycle,
        nest_manager,
        monsters,
        game_over_state,
        data.get("skill_points_available", 0),
        data.get("monsters_killed_this_night", 0),
    )


def _dump_grid(grid: Grid) -> dict:
    return {
        "width": grid.width,
        "height": grid.height,
        "tiles": [
            [{"resource": t.resource, "revealed": t.revealed, "claimed": t.claimed} for t in row]
            for row in grid.tiles
        ],
    }


def _load_grid(data: dict) -> Grid:
    grid = Grid.__new__(Grid)
    grid.width = data["width"]
    grid.height = data["height"]
    grid.tiles = [
        [Tile(resource=t["resource"], revealed=t["revealed"], claimed=t["claimed"]) for t in row]
        for row in data["tiles"]
    ]
    return grid
