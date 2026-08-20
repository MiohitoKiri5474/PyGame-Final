"""Pygame-free checkpoint save/load. Serializes the full simulation state
(grid, inventory, tasks, buildings, NPCs, nests, monsters, cycle, game-over)
to JSON so the game can resume across sessions/machines from a save file."""

import json
import random
from pathlib import Path

from animal import Animal
from build_task import Building
from day_night import DayNightCycle
from game_over import GameOverState
from grid import Grid, Tile
from inventory import Inventory, PerishableBatch
from magic import Spellbook
from monster import Monster
from nest import Nest, NestManager
from npc import NPC
from skills import new_skill_levels
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
        "grid": _dump_grid(world.grid),
        "inventory": world.inventory.items(),
        "spellbook_cooldowns": world.spellbook.cooldowns,
        "skills": world.skills,
        "inventory_ledger": [
            {"resource": b.resource, "expires_in": b.expires_in, "amount": b.amount}
            for b in world.inventory.ledger
        ],
        "buildings": [
            {
                "type": b.type, "x": b.x, "y": b.y, "block": b.block, "attack": b.attack,
                "growth_timer": b.growth_timer, "ready": b.ready,
                "assigned_animal_id": getattr(b, "assigned_animal_id", None),
            }
            for b in world.buildings
        ],
        "animals": [
            {
                "id": a.id,
                "x": a.x,
                "y": a.y,
                "species": a.species,
                "speed": a.speed,
                "dangerous": a.dangerous,
                "health": a.health,
                "is_hostile": a.is_hostile,
                "is_tamed": getattr(a, "is_tamed", False),
                "pen_tile": list(a.pen_tile) if getattr(a, "pen_tile", None) else None,
                "path": [list(p) for p in a.path],
                "tamer_npc_id": getattr(a, "tamer_npc_id", None),
                "is_following": getattr(a, "is_following", False),
                "is_mounted": getattr(a, "is_mounted", False),
            }
            for a in world.animals
        ],
        "animal_spawn_timer": world.animal_spawn_timer,
        "pen_production_timer": getattr(world, "pen_production_timer", 0.0),
        "tasks": [
            {
                "type": t.type,
                "target": list(t.target),
                "assigned_npc_id": t.assigned_npc.id if t.assigned_npc else None,
                "target_animal_id": getattr(t, "target_animal_id", None),
            }
            for t in world.tasks.tasks
        ],
        "npcs": [
            {
                "id": npc.id,
                "x": npc.x,
                "y": npc.y,
                "speed": npc.speed,
                "base_speed": npc.base_speed,
                "path": [list(p) for p in npc.path],
                "health": npc.health,
                "max_health": npc.max_health,
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
                "path": [list(p) for p in m.path],
                "health": m.health,
                "attack": m.attack,
                "defense": m.defense,
                "burn_ticks_remaining": m.burn_ticks_remaining,
                "burn_damage_per_tick": m.burn_damage_per_tick,
                "frozen_remaining": m.frozen_remaining,
                "type": m.type,
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
    world.wildlife_rng = random.Random()  # fresh, unseeded - same precedent as NestManager on load
    world.inventory = Inventory()
    for resource, amount in data["inventory"].items():
        world.inventory._counts[resource] = amount
    world.inventory.ledger = [
        PerishableBatch(resource=b["resource"], expires_in=b["expires_in"], amount=b["amount"])
        for b in data.get("inventory_ledger", [])
    ]
    world.spellbook = Spellbook(cooldowns=data.get("spellbook_cooldowns", {}))
    # {**defaults, **saved} guarantees every current skill name is present
    # even from an older save predating a since-added skill.
    world.skills = {**new_skill_levels(), **data.get("skills", {})}
    world.buildings = []
    for bd in data["buildings"]:
        building = Building(
            type=bd["type"], x=bd["x"], y=bd["y"], block=bd["block"], attack=bd["attack"],
            growth_timer=bd.get("growth_timer", 0.0), ready=bd.get("ready", False),
        )
        building.assigned_animal_id = bd.get("assigned_animal_id")
        world.buildings.append(building)

    world.animals = []
    max_animal_id = -1
    for ad in data.get("animals", []):
        animal = Animal(
            ad["x"], ad["y"], species=ad["species"], speed=ad["speed"],
            dangerous=ad["dangerous"], health=ad["health"], id=ad.get("id"),
        )
        animal.is_hostile = ad.get("is_hostile", False)
        animal.is_tamed = ad.get("is_tamed", False)
        animal.pen_tile = tuple(ad["pen_tile"]) if ad.get("pen_tile") else None
        animal.path = [tuple(p) for p in ad.get("path", [])]
        animal.tamer_npc_id = ad.get("tamer_npc_id")
        animal.is_following = ad.get("is_following", False)
        animal.is_mounted = ad.get("is_mounted", False)
        world.animals.append(animal)
        if animal.id is not None:
            max_animal_id = max(max_animal_id, animal.id)
    Animal._next_id = max(Animal._next_id, max_animal_id + 1)
    world.animal_spawn_timer = data.get("animal_spawn_timer", 0.0)
    world.pen_production_timer = data.get("pen_production_timer", 0.0)

    tasks = [
        Task(
            type=t["type"],
            target=tuple(t["target"]),
            target_animal_id=t.get("target_animal_id"),
        )
        for t in data["tasks"]
    ]
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
        # Explicit field, not re-derived from role: Defense Ability (ticket
        # 23) can raise max_health above the role's base value, and that
        # bonus must survive a reload. Falls back to the role-derived
        # default for saves predating this field.
        npc.max_health = nd.get("max_health", npc.max_health)
        # Fallback to the already-buffed speed for saves predating this
        # field - correct for a never-mounted/never-penned NPC, and the
        # worst case for others is a one-time bonus, not a compounding one
        # (tame_task._tick_pen_production now always recomputes from this).
        npc.base_speed = nd.get("base_speed", nd["speed"])
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
        monster.burn_ticks_remaining = md.get("burn_ticks_remaining", 0)
        monster.burn_damage_per_tick = md.get("burn_damage_per_tick", 0)
        monster.frozen_remaining = md.get("frozen_remaining", 0.0)
        # burn_tick_timer intentionally not persisted - sub-second timing
        # precision on a 3-second DoT isn't worth the extra save-file field;
        # a reloaded mid-burn monster just restarts its current tick's timer.
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
            [
                {
                    "resource": t.resource,
                    "revealed": t.revealed,
                    "claimed": t.claimed,
                    "terrain": getattr(t, "terrain", "plain"),
                }
                for t in row
            ]
            for row in grid.tiles
        ],
    }


def _load_grid(data: dict) -> Grid:
    grid = Grid.__new__(Grid)
    grid.width = data["width"]
    grid.height = data["height"]
    grid.tiles = [
        [
            Tile(
                resource=None if t.get("terrain", "plain") == "mountain" else t["resource"],
                revealed=t["revealed"],
                claimed=t["claimed"],
                terrain=t.get("terrain", "plain"),
            )
            for t in row
        ]
        for row in data["tiles"]
    ]
    return grid


