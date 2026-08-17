import math
import random

import pygame

from constants import (
    WINDOW_WIDTH,
    WINDOW_HEIGHT,
    FPS,
    TILE_SIZE,
    VIEWPORT_TILES_X,
    VIEWPORT_TILES_Y,
    NPC_RADIUS,
    NPC_MAX_HUNGER,
    NEST_INITIAL_COUNT,
    COLOR_BG,
    COLOR_FOG,
    COLOR_UNCLAIMED,
    COLOR_CLAIMED_EMPTY,
    COLOR_RESOURCE,
    COLOR_GRID_LINE,
    COLOR_TEXT,
    COLOR_DAY_BANNER,
    COLOR_NIGHT_BANNER,
    COLOR_NPC,
    COLOR_NPC_SELECTED,
    COLOR_MONSTER,
    COLOR_NEST,
    COLOR_HUNGER_BAR,
    COLOR_BAR_BG,
)
from camera import Camera
from combat import resolve_combat
from day_night import DayNightCycle, DAY
from coords import tile_at, tile_center
from nest import NestManager, create_initial_nests
from npc import NPC
from monster import spawn_monster
from pathfinding import find_path
from task import TASK_TYPES, update_npc_tasks
from extensions import hud_lines, render_overlays
from world import World
from priority_ui import PriorityTableUI


class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Colony Defense (WIP)")
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 24)

        self.world = World()
        self.camera = Camera()
        self.cycle = DayNightCycle()
        self.paused = False
        self.running = True

        self.selected_npc: NPC | None = None
        self.selected_task_type: str | None = next(iter(TASK_TYPES), None)
        self.priority_ui = PriorityTableUI()

        initial_nests = create_initial_nests(
            self.world.grid.width, self.world.grid.height, NEST_INITIAL_COUNT, random.Random()
        )
        self.nest_manager = NestManager(self.world.grid.width, self.world.grid.height, initial_nests)
        self.monsters = []

    def run(self) -> None:
        while self.running:
            dt = self.clock.tick(FPS) / 1000
            self.handle_events()
            self.update(dt)
            self.render()
        pygame.quit()

    def handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                # Priority UI intercepts keys when open
                if self.priority_ui.visible:
                    self.priority_ui.handle_key(event.key, self.world.npcs)
                    continue
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_SPACE:
                    self.paused = not self.paused
                elif event.key == pygame.K_TAB:
                    self._cycle_selected_task_type()
                elif event.key == pygame.K_p:
                    self.priority_ui.toggle()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if not self.priority_ui.visible:
                    self.handle_click(event.pos)

    def _cycle_selected_task_type(self) -> None:
        types = list(TASK_TYPES.keys())
        if not types:
            self.selected_task_type = None
            return
        if self.selected_task_type not in types:
            self.selected_task_type = types[0]
            return
        next_index = (types.index(self.selected_task_type) + 1) % len(types)
        self.selected_task_type = types[next_index]

    def handle_click(self, screen_pos: tuple[int, int]) -> None:
        world_x = screen_pos[0] + self.camera.x
        world_y = screen_pos[1] + self.camera.y

        clicked_npc = self._npc_at_world_pos(world_x, world_y)
        if clicked_npc is not None:
            self.selected_npc = clicked_npc
            return

        gx, gy = tile_at(world_x, world_y)
        if not self.world.grid.in_bounds(gx, gy):
            return

        task_type = TASK_TYPES.get(self.selected_task_type) if self.selected_task_type else None
        if task_type is not None and task_type.can_queue(self.world, (gx, gy)):
            self.world.tasks.add(self.selected_task_type, (gx, gy))

    def _npc_at_world_pos(self, wx: float, wy: float) -> NPC | None:
        for npc in self.world.npcs:
            if math.hypot(npc.x - wx, npc.y - wy) <= NPC_RADIUS * 1.5:
                return npc
        return None

    def update(self, dt: float) -> None:
        keys = pygame.key.get_pressed()
        dx = (keys[pygame.K_RIGHT] or keys[pygame.K_d]) - (keys[pygame.K_LEFT] or keys[pygame.K_a])
        dy = (keys[pygame.K_DOWN] or keys[pygame.K_s]) - (keys[pygame.K_UP] or keys[pygame.K_w])
        self.camera.pan(dx, dy, dt)  # camera pans even while paused

        if not self.paused:
            self.cycle.update(dt)
            update_npc_tasks(self.world, dt)

            for tile in self.nest_manager.update(dt, self.cycle.round_number, self.cycle.phase):
                self.monsters.append(spawn_monster(tile, self.world.grid, self.world.buildings))
            for monster in self.monsters:
                monster.update(dt)

            resolve_combat(self.world.npcs, self.monsters, self.world.buildings)
            self.world.npcs[:] = [npc for npc in self.world.npcs if not npc.is_dead]
            if self.selected_npc is not None and self.selected_npc.is_dead:
                self.selected_npc = None

    def render(self) -> None:
        self.screen.fill(COLOR_BG)
        self.render_grid()
        self.render_nests()
        self.render_npcs()
        self.render_monsters()
        render_overlays(self.screen, self.world, self.camera)
        self.render_hud()
        self.priority_ui.render(self.screen, self.font, self.world.npcs)
        pygame.display.flip()

    def render_npcs(self) -> None:
        cam_x, cam_y = self.camera.x, self.camera.y
        npc_radius = NPC_RADIUS
        bar_w = TILE_SIZE - 4
        bar_h = 4

        for npc in self.world.npcs:
            sx = int(npc.x - cam_x)
            sy = int(npc.y - cam_y)

            # Body
            pygame.draw.circle(self.screen, COLOR_NPC, (sx, sy), npc_radius)
            if npc is self.selected_npc:
                pygame.draw.circle(self.screen, COLOR_NPC_SELECTED, (sx, sy), npc_radius, 2)

            # Hunger bar (above the NPC)
            bar_x = sx - bar_w // 2
            bar_y = sy - npc_radius - bar_h - 4
            hunger_ratio = max(0.0, min(1.0, npc.hunger / NPC_MAX_HUNGER))
            # Background
            pygame.draw.rect(self.screen, COLOR_BAR_BG,
                             pygame.Rect(bar_x, bar_y, bar_w, bar_h))
            # Fill
            fill_w = max(0, int(bar_w * hunger_ratio))
            if fill_w > 0:
                pygame.draw.rect(self.screen, COLOR_HUNGER_BAR,
                                 pygame.Rect(bar_x, bar_y, fill_w, bar_h))

    def render_monsters(self) -> None:
        for monster in self.monsters:
            screen_x = int(monster.x - self.camera.x)
            screen_y = int(monster.y - self.camera.y)
            pygame.draw.circle(self.screen, COLOR_MONSTER, (screen_x, screen_y), NPC_RADIUS)

    def render_nests(self) -> None:
        for nest in self.nest_manager.nests:
            if not self.world.grid.get(nest.x, nest.y).revealed:
                continue
            screen_x = nest.x * TILE_SIZE - self.camera.x
            screen_y = nest.y * TILE_SIZE - self.camera.y
            rect = pygame.Rect(screen_x, screen_y, TILE_SIZE, TILE_SIZE)
            pygame.draw.rect(self.screen, COLOR_NEST, rect)

    def render_grid(self) -> None:
        cam_x, cam_y = self.camera.x, self.camera.y
        start_col = cam_x // TILE_SIZE
        start_row = cam_y // TILE_SIZE
        grid = self.world.grid

        for row in range(start_row, min(grid.height, start_row + VIEWPORT_TILES_Y + 2)):
            for col in range(start_col, min(grid.width, start_col + VIEWPORT_TILES_X + 2)):
                tile = grid.get(col, row)
                screen_x = col * TILE_SIZE - cam_x
                screen_y = row * TILE_SIZE - cam_y
                rect = pygame.Rect(screen_x, screen_y, TILE_SIZE, TILE_SIZE)

                if not tile.revealed:
                    color = COLOR_FOG
                elif not tile.claimed:
                    color = COLOR_UNCLAIMED
                elif tile.resource:
                    color = COLOR_RESOURCE
                else:
                    color = COLOR_CLAIMED_EMPTY

                pygame.draw.rect(self.screen, color, rect)
                pygame.draw.rect(self.screen, COLOR_GRID_LINE, rect, 1)

    def render_hud(self) -> None:
        banner_color = COLOR_DAY_BANNER if self.cycle.phase == DAY else COLOR_NIGHT_BANNER
        lines = [
            f"Round {self.cycle.round_number} - {self.cycle.phase.upper()}  ({self.cycle.remaining():.0f}s)",
            f"NPCs alive: {len(self.world.npcs)}",
            "PAUSED" if self.paused else "",
            f"Selected task: {self.selected_task_type or 'none'}  [Tab to cycle]",
            *hud_lines(self.world),
        ]
        y = 8
        for i, text in enumerate(lines):
            if not text:
                continue
            color = banner_color if i == 0 else COLOR_TEXT
            surf = self.font.render(text, True, color)
            self.screen.blit(surf, (8, y))
            y += surf.get_height() + 4
