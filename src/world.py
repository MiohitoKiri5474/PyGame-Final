import plugins  # noqa: F401  # side effect: populates task.TASK_TYPES via plugins.py

from constants import STARTING_NPC_COUNT
from coords import tile_center
from grid import Grid
from inventory import Inventory
from npc import NPC
from task import TaskQueue


class World:
    def __init__(self, npc_count: int = STARTING_NPC_COUNT):
        self.grid = Grid()
        self.inventory = Inventory()
        self.tasks = TaskQueue()

        center_x, center_y = self.grid.width // 2, self.grid.height // 2
        self.npcs: list[NPC] = [
            NPC(*tile_center(center_x + i - npc_count // 2, center_y), id=i) for i in range(npc_count)
        ]
