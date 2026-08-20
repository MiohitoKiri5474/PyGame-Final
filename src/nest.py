import random

from constants import (
    MONSTER_SPAWN_WEIGHTS,
    NEST_BASE_SPAWN_INTERVAL,
    NEST_MAX_COUNT,
    NEST_MIN_SPAWN_INTERVAL,
    NEST_SPAWN_RAMP_PER_ROUND,
    NEW_NEST_INTERVAL,
)
from day_night import NIGHT

Tile = tuple[int, int]


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


def create_initial_nests(width: int, height: int, count: int, rng: random.Random) -> list[Nest]:
    """Place nests on the map edge, away from the center where NPCs start."""
    chosen = rng.sample(_edge_tiles(width, height), min(count, width * 2 + height * 2))
    return [Nest(x, y) for x, y in chosen]


class NestManager:
    def __init__(
        self,
        width: int,
        height: int,
        nests: list[Nest] | None = None,
        rng: random.Random | None = None,
    ):
        self.width = width
        self.height = height
        self.nests = list(nests) if nests else []
        self.rng = rng or random.Random()
        self.new_nest_timer = 0.0

    def on_night_start(self, round_number: int) -> None:
        """Called upon nightfall to prime nests so vanguard monsters emerge early."""
        for nest in self.nests:
            # Prime spawn timer so the first wave emerges within 3-4s of nightfall
            nest.spawn_timer = max(0.0, nest.spawn_interval(round_number) - 4.0)

    def update(self, dt: float, round_number: int, phase: str) -> list[Tile]:
        spawn_tiles: list[Tile] = []
        if phase == NIGHT:
            for nest in self.nests:
                if nest.update(dt, round_number):
                    spawn_tiles.append((nest.x, nest.y))

        self.new_nest_timer += dt
        if self.new_nest_timer >= NEW_NEST_INTERVAL and len(self.nests) < NEST_MAX_COUNT:
            self.new_nest_timer = 0.0
            occupied = {(nest.x, nest.y) for nest in self.nests}
            candidates = [t for t in _edge_tiles(self.width, self.height) if t not in occupied]
            if candidates:
                self.nests.append(Nest(*self.rng.choice(candidates)))

        return spawn_tiles

    def pick_monster_type(self) -> str:
        return self.rng.choices(
            list(MONSTER_SPAWN_WEIGHTS), weights=list(MONSTER_SPAWN_WEIGHTS.values())
        )[0]
