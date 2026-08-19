import random

from coords import tile_at
from movement import step_toward_path


class Animal:
    """Neutral wildlife: wanders passively, never proximity-aggroes. Dangerous
    species (Wolf/Bear) only retaliate after being attacked first."""

    _next_id = 0

    def __init__(
        self,
        x: float,
        y: float,
        species: str,
        speed: float,
        dangerous: bool,
        health: int,
        rng: random.Random | None = None,
        id: int | None = None,
    ):
        if id is not None:
            self.id = id
            Animal._next_id = max(Animal._next_id, id + 1)
        else:
            self.id = Animal._next_id
            Animal._next_id += 1

        self.x = x
        self.y = y
        self.species = species
        self.speed = speed
        self.dangerous = dangerous
        self.health = health
        self.max_health = health
        self.is_hostile = False
        self.is_tamed = False
        self.pen_tile: tuple[int, int] | None = None
        self.path: list[tuple[int, int]] = []
        self._rng = rng or random.Random()

        # Paper Mario Animation & Combat states
        self.facing_left = False
        self.display_facing_left = False
        self.flip_progress = 1.0
        self.anim_timer = 0.0
        self.is_moving = False
        self.attack_timer = 0.0
        self.hit_timer = 0.0
        self.combat_target: tuple[float, float] | None = None

    @property
    def has_arrived(self) -> bool:
        return not self.path

    @property
    def is_dead(self) -> bool:
        return self.health <= 0


    def trigger_attack(self, target_x: float, target_y: float) -> None:
        """Trigger an attack/bite/claw strike towards target."""
        self.attack_timer = 0.35
        self.combat_target = (target_x, target_y)
        if target_x < self.x:
            self.facing_left = True
            self.display_facing_left = True
        elif target_x > self.x:
            self.facing_left = False
            self.display_facing_left = False

    def trigger_hit(self) -> None:
        """Trigger a damage reaction squash & hurt flash."""
        self.hit_timer = 0.25

    def take_damage(self, amount: float) -> None:
        self.health -= amount
        self.trigger_hit()
        if self.dangerous:
            self.is_hostile = True

    def retaliate(self, npc) -> float:
        """Dangerous hostile animals deal retaliation damage to the attacking NPC."""
        if not self.dangerous or not self.is_hostile or npc is None:
            return 0.0
        self.trigger_attack(npc.x, npc.y)
        if hasattr(npc, "trigger_hit"):
            npc.trigger_hit()
        animal_attack = 18 if self.species == "Bear" else (10 if self.species == "Wolf" else 5)
        dmg = max(1, animal_attack - getattr(npc, "defense", 0))
        npc.health -= dmg
        return dmg

    def set_path(self, path: list[tuple[int, int]]) -> None:
        self.path = list(path)

    def update(self, dt: float, grid_width: int, grid_height: int) -> None:
        self.attack_timer = max(0.0, self.attack_timer - dt)
        self.hit_timer = max(0.0, self.hit_timer - dt)

        if not self.path:
            cx, cy = tile_at(self.x, self.y)
            dx, dy = self._rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
            nx, ny = cx + dx, cy + dy
            if 0 <= nx < grid_width and 0 <= ny < grid_height:
                self.set_path([(nx, ny)])

        old_x = self.x
        self.x, self.y, self.path = step_toward_path(self.x, self.y, self.path, self.speed, dt)
        dx = self.x - old_x
        if abs(dx) > 0.01:
            new_facing = (dx < 0.0)
            if new_facing != self.facing_left:
                self.facing_left = new_facing
                self.flip_progress = 0.0

        if self.flip_progress < 1.0:
            self.flip_progress = min(1.0, self.flip_progress + dt * 8.0)
            if self.flip_progress >= 0.5:
                self.display_facing_left = self.facing_left
        else:
            self.display_facing_left = self.facing_left

        if not self.has_arrived:
            self.is_moving = True
            self.anim_timer += dt
        else:
            self.is_moving = False

