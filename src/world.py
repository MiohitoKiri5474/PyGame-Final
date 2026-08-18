import plugins  # noqa: F401  # side effect: populates task.TASK_TYPES via plugins.py

import random

from constants import ANIMAL_INITIAL_COUNT, ROLES, STARTING_NPC_COUNT
from coords import tile_center
from grid import Grid
from inventory import Inventory
from magic import Spellbook
from npc import NPC
from task import TaskQueue
from wildlife import create_initial_animals


class World:
    def __init__(self, npc_count: int = STARTING_NPC_COUNT):
        self.grid = Grid()
        self.inventory = Inventory()
        self.tasks = TaskQueue()
        self.buildings: list = []
        self.spellbook = Spellbook()
        # Same rng-injection pattern as NestManager.rng - seedable/testable,
        # reused (not re-created per spawn) for the periodic top-up in
        # wildlife._tick_wildlife.
        self.wildlife_rng = random.Random()
        self.animals = create_initial_animals(self.grid, ANIMAL_INITIAL_COUNT, rng=self.wildlife_rng)
        self.animal_spawn_timer = 0.0

        center_x, center_y = self.grid.width // 2, self.grid.height // 2
        # Round-robin over ROLES so the default 3-NPC start is exactly
        # 1 Farmer/1 Knight/1 Mage, not random.
        self.npcs: list[NPC] = [
            NPC(*tile_center(center_x + i - npc_count // 2, center_y), role=ROLES[i % len(ROLES)])
            for i in range(npc_count)
        ]
