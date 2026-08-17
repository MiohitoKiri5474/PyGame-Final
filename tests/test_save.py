from build_task import Building
from day_night import DayNightCycle, NIGHT
from game_over import GameOverState
from monster import Monster
from nest import Nest, NestManager
from npc import NPC
from save import dump_state, load_checkpoint, save_checkpoint
from task import Task
from world import World


def _build_nontrivial_state():
    world = World(npc_count=0)
    world.grid.get(5, 5).claimed = True
    world.grid.get(5, 5).revealed = True
    world.grid.get(6, 6).revealed = True
    world.grid.get(6, 6).claimed = False
    world.inventory.add("crop", 7)
    world.buildings.append(Building(type="Wall", x=5, y=5, block=100, attack=0))

    idle_task = world.tasks.add("Gather", (6, 6))

    npc_a = NPC(160.0, 160.0, priority=["Gather", "BuildWall"])
    npc_a.health = 42
    npc_a.hunger = 55.5
    npc_a.attack = 12
    npc_a.defense = 4
    npc_a.set_path([(5, 5), (6, 6)])
    npc_b = NPC(320.0, 320.0)
    npc_b.task_progress = 1.5
    world.npcs = [npc_a, npc_b]

    assigned_task = world.tasks.add("BuildWall", (7, 7))
    assigned_task.assigned_npc = npc_b
    npc_b.task = assigned_task

    # World(npc_count=0) already auto-spawns initial wildlife; pin one to
    # known values instead of relying on its random species/position
    animal = world.animals[0]
    animal.species = "Bear"
    animal.dangerous = True
    animal.health = 45
    animal.is_hostile = True
    animal.set_path([(8, 8)])
    world.animal_spawn_timer = 17.5

    cycle = DayNightCycle()
    cycle.round_number = 3
    cycle.phase = NIGHT
    cycle.timer = 12.5

    nest = Nest(0, 5)
    nest.spawn_timer = 3.25
    nest_manager = NestManager(world.grid.width, world.grid.height, nests=[nest])
    nest_manager.new_nest_timer = 40.0

    monster = Monster(300.0, 400.0)
    monster.set_path([(9, 9), (10, 10)])
    monster.health = 17

    game_over_state = GameOverState()

    return world, cycle, nest_manager, [monster], game_over_state, idle_task


def test_dump_state_round_trips_through_save_and_load(tmp_path):
    world, cycle, nest_manager, monsters, game_over_state, _ = _build_nontrivial_state()
    path = tmp_path / "save.json"

    dump_before = dump_state(world, cycle, nest_manager, monsters, game_over_state)
    save_checkpoint(world, cycle, nest_manager, monsters, game_over_state, path=path)
    loaded_world, loaded_cycle, loaded_nests, loaded_monsters, loaded_game_over = load_checkpoint(path)
    dump_after = dump_state(loaded_world, loaded_cycle, loaded_nests, loaded_monsters, loaded_game_over)

    assert dump_before == dump_after


def test_round_trip_preserves_specific_field_values(tmp_path):
    world, cycle, nest_manager, monsters, game_over_state, _ = _build_nontrivial_state()
    path = tmp_path / "save.json"
    save_checkpoint(world, cycle, nest_manager, monsters, game_over_state, path=path)
    loaded_world, loaded_cycle, loaded_nests, loaded_monsters, _ = load_checkpoint(path)

    npc_a = next(n for n in loaded_world.npcs if n.health == 42)
    assert npc_a.hunger == 55.5

    npc_b = next(n for n in loaded_world.npcs if n is not npc_a)
    assert npc_b.task_progress == 1.5
    assert npc_b.task is not None
    assert npc_b.task.assigned_npc is npc_b  # bidirectional link rebuilt, not duplicated

    assert loaded_world.grid.get(5, 5).claimed is True
    assert loaded_world.grid.get(6, 6).claimed is False
    assert loaded_world.grid.get(6, 6).revealed is True
    assert loaded_world.inventory.get("crop") == 7
    assert loaded_nests.nests[0].spawn_timer == 3.25
    assert loaded_cycle.timer == 12.5
    assert loaded_monsters[0].health == 17

    loaded_bear = next(a for a in loaded_world.animals if a.species == "Bear")
    assert loaded_bear.dangerous is True
    assert loaded_bear.health == 45
    assert loaded_bear.is_hostile is True
    assert loaded_bear.path == [(8, 8)]
    assert len(loaded_world.animals) == len(world.animals)
    assert loaded_world.animal_spawn_timer == 17.5


def test_round_trip_preserves_tuple_types_not_lists(tmp_path):
    world, cycle, nest_manager, monsters, game_over_state, _ = _build_nontrivial_state()
    path = tmp_path / "save.json"
    save_checkpoint(world, cycle, nest_manager, monsters, game_over_state, path=path)
    loaded_world, _, _, loaded_monsters, _ = load_checkpoint(path)

    for task in loaded_world.tasks.tasks:
        assert isinstance(task.target, tuple)
    for npc in loaded_world.npcs:
        assert all(isinstance(p, tuple) for p in npc.path)
    for monster in loaded_monsters:
        assert all(isinstance(p, tuple) for p in monster.path)
    for animal in loaded_world.animals:
        assert all(isinstance(p, tuple) for p in animal.path)


def test_load_with_no_file_returns_none(tmp_path):
    assert load_checkpoint(tmp_path / "missing.json") is None


def test_load_with_corrupt_file_returns_none(tmp_path):
    path = tmp_path / "save.json"
    path.write_text('{"round_number": 1, "phase": "day"')  # truncated mid-write
    assert load_checkpoint(path) is None


def test_load_dangling_assigned_npc_id_leaves_task_reclaimable(tmp_path):
    """If a task was assigned to an NPC that died and dropped out of
    world.npcs before the save fired, that NPC's id won't appear in the
    saved npc list. The task must come back unassigned, not permanently
    stuck (same starvation class fixed for Expand in ticket 03)."""
    world, cycle, nest_manager, monsters, game_over_state, idle_task = _build_nontrivial_state()
    ghost_task = Task(type="Gather", target=(1, 1), assigned_npc=None)
    ghost_task.assigned_npc = type("Ghost", (), {"id": 9999})()
    world.tasks.tasks.append(ghost_task)
    path = tmp_path / "save.json"

    save_checkpoint(world, cycle, nest_manager, monsters, game_over_state, path=path)
    loaded_world, *_ = load_checkpoint(path)

    reloaded_ghost_task = next(t for t in loaded_world.tasks.tasks if t.target == (1, 1))
    assert reloaded_ghost_task.assigned_npc is None
