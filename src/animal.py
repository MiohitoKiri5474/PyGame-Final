import random

from coords import tile_at
from movement import step_toward_path


class Animal:
    """Neutral wildlife: wanders passively, never proximity-aggroes. Dangerous
    species (Wolf/Bear) only retaliate after being attacked first."""

    def __init__(
        self,
        x: float,
        y: float,
        species: str,
        speed: float,
        dangerous: bool,
        health: int,
        rng: random.Random | None = None,
    ):
        self.x = x
        self.y = y
        self.species = species
        self.speed = speed
        self.dangerous = dangerous
        self.health = health
        self.is_hostile = False
        self.path: list[tuple[int, int]] = []
        self._rng = rng or random.Random()

    @property
    def is_dead(self) -> bool:
        return self.health <= 0

    def take_damage(self, amount: float) -> None:
        self.health -= amount
        if self.dangerous:
            self.is_hostile = True

    def set_path(self, path: list[tuple[int, int]]) -> None:
        self.path = list(path)

    def update(self, dt: float, grid_width: int, grid_height: int) -> None:
        if not self.path:
            cx, cy = tile_at(self.x, self.y)
            dx, dy = self._rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
            nx, ny = cx + dx, cy + dy
            if 0 <= nx < grid_width and 0 <= ny < grid_height:
                self.set_path([(nx, ny)])
        self.x, self.y, self.path = step_toward_path(self.x, self.y, self.path, self.speed, dt)
