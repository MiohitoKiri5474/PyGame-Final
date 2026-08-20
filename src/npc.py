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
    MUD_IMMOBILIZE_DURATION,
    RIVER_SPEED_MULTIPLIER,
    SCORCHED_BURN_DPS,
    TERRAIN_MUD,
    TERRAIN_RIVER,
    TERRAIN_SCORCHED,
)

from coords import tile_at
from movement import step_toward_path

DEFAULT_SPEED = 150.0  # pixels/sec (scaled with the TILE_SIZE 32->40 zoom bump, same tiles/sec pacing)


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
        # One tick behind self.x/y - a tamed animal following this NPC trails
        # this instead of the live position (snake-follow style), so it
        # naturally retraces where the NPC actually walked.
        self.prev_x = x
        self.prev_y = y
        self.speed = speed
        # Unbuffed speed - tame_task._tick_pen_production recomputes self.speed
        # from this every tick, so anything that grants a temporary bonus
        # (pen buff, mount) must add on top of base_speed, never overwrite it.
        self.base_speed = speed
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


        # Environmental Hazard states
        self.immobilized_timer: float = 0.0
        self.last_mud_tile: tuple[int, int] | None = None
        self.is_burning: bool = False
        self.is_in_river: bool = False

        # Paper Mario Animation states
        self.facing_left = False
        self.is_moving = False
        self.anim_timer = 0.0
        self.work_anim_timer = 0.0
        self.flip_progress = 1.0
        self.display_facing_left = False
        self.attack_timer = 0.0
        self.hit_timer = 0.0
        self.attack_cooldown = 0.0
        self.combat_target: tuple[float, float] | None = None
        # Gates how often combat.resolve_combat lets this NPC land a hit -
        # separate from attack_timer above, which is purely the swing
        # animation's visual duration and never gated combat before.
        self.attack_cooldown = 0.0

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

    def update(self, dt: float, grid=None) -> None:
        """Advance one simulation tick. Hunger decays continuously;
        starvation kills when hunger reaches 0."""
        self.prev_x, self.prev_y = self.x, self.y
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
            self.attack_cooldown = 0.0
            return

        self.attack_timer = max(0.0, self.attack_timer - dt)
        self.hit_timer = max(0.0, self.hit_timer - dt)
        self.attack_cooldown = max(0.0, self.attack_cooldown - dt)

        # Environmental Terrain Hazards & Status Effects
        cur_terrain = "plain"
        tx, ty = tile_at(self.x, self.y)
        if grid is not None and grid.in_bounds(tx, ty):
            tile = grid.get(tx, ty)
            cur_terrain = getattr(tile, "terrain", "plain")

        # 1. Mud Terrain: Immobilize for 5 seconds upon entering a new mud tile
        if cur_terrain == TERRAIN_MUD:
            if self.last_mud_tile != (tx, ty):
                self.immobilized_timer = MUD_IMMOBILIZE_DURATION
                self.last_mud_tile = (tx, ty)
        else:
            self.last_mud_tile = None

        if self.immobilized_timer > 0.0:
            self.immobilized_timer = max(0.0, self.immobilized_timer - dt)

        # 2. Scorched Earth Terrain: Burn damage over time + Burning VFX
        if cur_terrain == TERRAIN_SCORCHED:
            self.is_burning = True
            self.health = max(0.0, self.health - SCORCHED_BURN_DPS * dt)
            if self.health <= 0.0:
                self.kill()
                return
        else:
            self.is_burning = False

        # 3. River Terrain: Slowdown
        self.is_in_river = (cur_terrain == TERRAIN_RIVER)

        # Movement Speed determination
        if self.immobilized_timer > 0.0:
            effective_speed = 0.0
        elif self.is_in_river:
            effective_speed = self.speed * RIVER_SPEED_MULTIPLIER
        else:
            effective_speed = self.speed

        old_x = self.x
        self.x, self.y, self.path = step_toward_path(self.x, self.y, self.path, effective_speed, dt)
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



