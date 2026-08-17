"""NPC entity — minimal implementation for hunger/starvation (ticket 08).

Future tickets will extend this with pathfinding (01), task execution (02),
role stats (role-split), and combat (06).
"""

from constants import NPC_MAX_HEALTH, NPC_MAX_HUNGER, HUNGER_DECAY_RATE


class NPC:
    """A single controllable character in the colony."""

    _next_id = 0

    def __init__(self, x: float, y: float):
        self.id = NPC._next_id
        NPC._next_id += 1

        # Position (pixels)
        self.x = x
        self.y = y

        # Vitals
        self.health = NPC_MAX_HEALTH
        self.hunger = NPC_MAX_HUNGER
        self.alive = True

    # ------------------------------------------------------------------
    # Tick
    # ------------------------------------------------------------------

    def update(self, dt: float) -> None:
        """Advance one simulation tick.  Hunger decays continuously;
        starvation kills when hunger reaches 0."""
        if not self.alive:
            return
        self.hunger = max(0.0, self.hunger - HUNGER_DECAY_RATE * dt)
        if self.hunger <= 0.0:
            self.kill()

    # ------------------------------------------------------------------
    # Death — shared path for starvation AND future combat death
    # ------------------------------------------------------------------

    def kill(self) -> None:
        """Mark this NPC as dead.  Called by starvation check above and,
        in the future, by combat damage when health reaches 0."""
        self.alive = False
