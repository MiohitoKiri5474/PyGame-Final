from constants import (
    NPC_MAX_HEALTH,
    NPC_MAX_HUNGER,
    HUNGER_DECAY_RATE,
    NPC_ATTACK,
    NPC_DEFENSE,
)
from movement import step_toward_path

DEFAULT_SPEED = 120.0  # pixels/sec


class NPC:
    """A single controllable character in the colony."""

    _next_id = 0

    def __init__(
        self,
        x: float,
        y: float,
        speed: float = DEFAULT_SPEED,
        priority: list[str] | None = None,
    ):
        self.id = NPC._next_id
        NPC._next_id += 1

        self.x = x
        self.y = y
        self.speed = speed
        self.path: list[tuple[int, int]] = []
        self.health = NPC_MAX_HEALTH
        self.hunger = NPC_MAX_HUNGER
        self.alive = True
        self.attack = NPC_ATTACK
        self.defense = NPC_DEFENSE
        self.priority = priority  # None = fall back to task-type registration order
        self.task = None  # set by task.update_npc_tasks; typed loosely to avoid a task.py<->npc.py import cycle
        self.task_progress = 0.0

    @property
    def has_arrived(self) -> bool:
        return not self.path

    @property
    def is_dead(self) -> bool:
        return not self.alive or self.health <= 0 or self.hunger <= 0

    def kill(self) -> None:
        """Mark this NPC as dead. Called by starvation and combat."""
        self.alive = False

    def set_path(self, path: list[tuple[int, int]]) -> None:
        self.path = list(path)

    def update(self, dt: float) -> None:
        """Advance one simulation tick. Hunger decays continuously;
        starvation kills when hunger reaches 0."""
        if not self.alive or self.health <= 0 or self.hunger <= 0:
            self.alive = False
            return
        self.hunger = max(0.0, self.hunger - HUNGER_DECAY_RATE * dt)
        if self.hunger <= 0.0:
            self.kill()
            return
        self.x, self.y, self.path = step_toward_path(self.x, self.y, self.path, self.speed, dt)
