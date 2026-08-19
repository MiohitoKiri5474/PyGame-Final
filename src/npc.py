from constants import (
    NPC_MAX_HEALTH,
    NPC_MAX_HUNGER,
    HUNGER_DECAY_RATE,
    HUNGER_RESTORE_PER_CROP,
    NPC_ATTACK,
    NPC_DEFENSE,
    COMBAT_RANGE,
    ROLE_STATS,
    SANCTUARY_HEAL_RATE,
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
        role: str | None = None,
    ):
        self.id = NPC._next_id
        NPC._next_id += 1

        self.x = x
        self.y = y
        self.speed = speed
        self.path: list[tuple[int, int]] = []
        self.role = role

        stats = ROLE_STATS.get(role)
        if stats is None:
            self.attack = NPC_ATTACK
            self.defense = NPC_DEFENSE
            self.max_health = NPC_MAX_HEALTH
            self.combat_range = COMBAT_RANGE
            self.work_multiplier = 1.0
        else:
            self.attack = stats["attack"]
            self.defense = stats["defense"]
            self.max_health = stats["max_health"]
            self.combat_range = stats["combat_range"]
            self.work_multiplier = stats["work_multiplier"]

        self.health = self.max_health
        self.hunger = NPC_MAX_HUNGER
        self.alive = True
        self.is_resting = False
        self.sanctuary_orig_pos: tuple[float, float] | None = None
        self.priority = priority  # None = fall back to task-type registration order

        self.task = None  # set by task.update_npc_tasks; typed loosely to avoid a task.py<->npc.py import cycle
        self.task_progress = 0.0


        # Paper Mario Animation states
        self.facing_left = False
        self.is_moving = False
        self.anim_timer = 0.0
        self.work_anim_timer = 0.0
        self.flip_progress = 1.0
        self.display_facing_left = False
        self.attack_timer = 0.0
        self.hit_timer = 0.0
        self.combat_target: tuple[float, float] | None = None

    @property
    def has_arrived(self) -> bool:
        return not self.path

    @property
    def is_dead(self) -> bool:
        return not self.alive or self.health <= 0 or self.hunger <= 0

    def kill(self) -> None:
        """Mark this NPC as dead. Called by starvation and combat."""
        self.alive = False

    def eat(self, amount: float = HUNGER_RESTORE_PER_CROP) -> None:
        """Consume food to restore hunger, capped at NPC_MAX_HUNGER."""
        if not self.alive or self.is_dead:
            return
        self.hunger = min(NPC_MAX_HUNGER, self.hunger + amount)

    def set_path(self, path: list[tuple[int, int]]) -> None:
        self.path = list(path)

    def trigger_attack(self, target_x: float, target_y: float) -> None:
        """Trigger an attack animation directed towards target."""
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

        if self.is_resting:
            # Sanctuary Resting: Regenerate health, clear movement/tasks, hunger still decays
            self.health = min(float(self.max_health), self.health + SANCTUARY_HEAL_RATE * dt)
            self.is_moving = False
            self.path = []
            self.attack_timer = 0.0
            self.hit_timer = 0.0
            return

        self.attack_timer = max(0.0, self.attack_timer - dt)
        self.hit_timer = max(0.0, self.hit_timer - dt)


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
            if self.task is not None:
                self.work_anim_timer += dt
            else:
                self.work_anim_timer = 0.0


