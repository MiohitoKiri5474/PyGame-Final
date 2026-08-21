import random

from blocking import is_mountain_blocked
from constants import (
    MONSTER_SPAWN_WEIGHTS,
    NEST_BASE_SPAWN_INTERVAL,
    NEST_FIRST_SPAWN_DELAY,
    NEST_MAX_COUNT,
    NEST_MIN_SPAWN_INTERVAL,
    NEST_SPAWN_COUNT_BASE,
    NEST_SPAWN_COUNT_MAX,
    NEST_SPAWN_COUNT_ROUNDS_PER_STEP,
    NEST_SPAWN_RAMP_PER_ROUND,
    NEW_NEST_INTERVAL,
)
from day_night import NIGHT

Tile = tuple[int, int]


def monsters_per_spawn(round_number: int) -> int:
    """How many monsters a single nest firing produces - ramps up
    alongside the interval-shrink in Nest.spawn_interval so later rounds
    get hit by both a faster cadence and a bigger burst each time."""
    step = (round_number - 1) // NEST_SPAWN_COUNT_ROUNDS_PER_STEP
    return min(NEST_SPAWN_COUNT_MAX, NEST_SPAWN_COUNT_BASE + step)


class Nest:
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y
        self.spawn_timer = 0.0

    def spawn_interval(self, round_number: int) -> float:
        interval = NEST_BASE_SPAWN_INTERVAL - NEST_SPAWN_RAMP_PER_ROUND * (round_number - 1)
        return max(NEST_MIN_SPAWN_INTERVAL, interval)

    def update(self, dt: float, round_number: int) -> bool:
        """Advance this nest's spawn timer; returns True the tick it fires."""
        self.spawn_timer += dt
        if self.spawn_timer >= self.spawn_interval(round_number):
            self.spawn_timer = 0.0
            return True
        return False


def _edge_tiles(width: int, height: int) -> list[Tile]:
    tiles = [(x, 0) for x in range(width)] + [(x, height - 1) for x in range(width)]
    tiles += [(0, y) for y in range(height)] + [(width - 1, y) for y in range(height)]
    return tiles


def _frontier_tiles(grid) -> list[Tile]:
    """Unrevealed tiles adjacent to a revealed one - the boundary of what
    the player has actually explored so far, as opposed to the far outer
    edge of the whole fixed map. Nests placed here track outward as fog
    gets cleared, so night threat scales with the player's own progress
    instead of starting (and staying) a fixed, possibly huge, distance away."""
    frontier = []
    for y in range(grid.height):
        for x in range(grid.width):
            if grid.get(x, y).revealed:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if grid.in_bounds(nx, ny) and grid.get(nx, ny).revealed:
                    frontier.append((x, y))
                    break
    return frontier


def _placeable(tiles: list[Tile], grid) -> list[Tile]:
    """Drop any tile a nest can't actually sit on: mountain terrain (the
    monsters it spawns would start on impassable ground and be stuck there
    forever, unable to path anywhere - same reason monster movement and
    task placement elsewhere in the codebase check is_mountain_blocked) or
    a tile carrying a resource (crop, wood, ...) - a nest sitting on top of
    one would block gathering it and look like it belongs there. No-op
    when there's no grid to check against."""
    if grid is None:
        return tiles
    return [
        t for t in tiles
        if grid.get(*t).resource is None and not is_mountain_blocked(grid, *t)
    ]


def create_initial_nests(
    width: int, height: int, count: int, rng: random.Random, grid=None
) -> list[Nest]:
    """Place nests just outside explored territory (or the map edge if no
    grid is given, or nothing's revealed yet) - away from the center where
    NPCs start."""
    candidates = _placeable(_frontier_tiles(grid), grid) if grid is not None else None
    candidates = candidates or _placeable(_edge_tiles(width, height), grid)
    chosen = rng.sample(candidates, min(count, len(candidates)))
    return [Nest(x, y) for x, y in chosen]


class NestManager:
    def __init__(
        self,
        width: int,
        height: int,
        nests: list[Nest] | None = None,
        rng: random.Random | None = None,
        grid=None,
    ):
        self.width = width
        self.height = height
        self.nests = list(nests) if nests else []
        self.rng = rng or random.Random()
        self.new_nest_timer = 0.0
        # Optional live grid reference - when set, new nests added over time
        # (below) follow the *current* explored-territory frontier rather
        # than the fixed map edge, same reasoning as create_initial_nests.
        self.grid = grid
        # Guarantees the first monster of each night appears quickly rather
        # than making the player wait out a full (round 1: 40s) spawn_interval
        # in total silence right as night falls - armed on the day->night
        # edge, independent of any individual nest's own timer state.
        self._was_night = False
        self._first_spawn_timer: float | None = None

    def on_night_start(self, round_number: int) -> None:
        """Called upon nightfall to prime nests so vanguard monsters emerge early."""
        for nest in self.nests:
            # Prime spawn timer so the first wave emerges within 3-4s of nightfall
            nest.spawn_timer = max(0.0, nest.spawn_interval(round_number) - 4.0)

    def update(self, dt: float, round_number: int, phase: str) -> list[Tile]:
        spawn_tiles: list[Tile] = []
        is_night = phase == NIGHT
        if is_night and not self._was_night and self.nests:
            self._first_spawn_timer = NEST_FIRST_SPAWN_DELAY
        self._was_night = is_night

        if is_night:
            if self._first_spawn_timer is not None:
                self._first_spawn_timer -= dt
                if self._first_spawn_timer <= 0.0:
                    self._first_spawn_timer = None
                    nest = self.rng.choice(self.nests)
                    spawn_tiles.extend([(nest.x, nest.y)] * monsters_per_spawn(round_number))

            count = monsters_per_spawn(round_number)
            for nest in self.nests:
                if nest.update(dt, round_number):
                    spawn_tiles.extend([(nest.x, nest.y)] * count)

        self.new_nest_timer += dt
        if self.new_nest_timer >= NEW_NEST_INTERVAL and len(self.nests) < NEST_MAX_COUNT:
            self.new_nest_timer = 0.0
            occupied = {(nest.x, nest.y) for nest in self.nests}
            candidates = (
                _placeable(_frontier_tiles(self.grid), self.grid) if self.grid is not None else None
            )
            candidates = candidates or _placeable(_edge_tiles(self.width, self.height), self.grid)
            candidates = [t for t in candidates if t not in occupied]
            if candidates:
                self.nests.append(Nest(*self.rng.choice(candidates)))

        return spawn_tiles

    def pick_monster_type(self) -> str:
        return self.rng.choices(
            list(MONSTER_SPAWN_WEIGHTS), weights=list(MONSTER_SPAWN_WEIGHTS.values())
        )[0]
