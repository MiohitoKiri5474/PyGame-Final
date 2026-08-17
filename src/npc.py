from constants import NPC_MAX_HEALTH, NPC_ATTACK, NPC_DEFENSE
from movement import step_toward_path

DEFAULT_SPEED = 120.0  # pixels/sec


class NPC:
    def __init__(
        self,
        x: float,
        y: float,
        speed: float = DEFAULT_SPEED,
        priority: list[str] | None = None,
        id: int = 0,
    ):
        self.x = x
        self.y = y
        self.speed = speed
        self.path: list[tuple[int, int]] = []
        self.health = NPC_MAX_HEALTH
        self.attack = NPC_ATTACK
        self.defense = NPC_DEFENSE
        self.priority = priority  # None = fall back to task-type registration order
        self.id = id  # stable across the NPC's life, unlike its position in world.npcs (which combat.py splices on death)
        self.task = None  # set by task.update_npc_tasks; typed loosely to avoid a task.py<->npc.py import cycle
        self.task_progress = 0.0

    @property
    def has_arrived(self) -> bool:
        return not self.path

    @property
    def is_dead(self) -> bool:
        return self.health <= 0

    def set_path(self, path: list[tuple[int, int]]) -> None:
        self.path = list(path)

    def update(self, dt: float) -> None:
        self.x, self.y, self.path = step_toward_path(self.x, self.y, self.path, self.speed, dt)
