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
    STARTING_NPC_COUNT,
    NPC_RADIUS,
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
)
from grid import Grid
from camera import Camera
from combat import resolve_combat
from day_night import DayNightCycle, DAY
from coords import tile_at, tile_center
from nest import NestManager, create_initial_nests
from npc import NPC
from monster import spawn_monster
from pathfinding import find_path


class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Colony Defense (WIP)")
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 24)

        self.grid = Grid()
        self.camera = Camera()
        self.cycle = DayNightCycle()
        self.paused = False
        self.running = True

        center = (self.grid.width // 2, self.grid.height // 2)
        self.npcs = [
            NPC(*tile_center(center[0] + i - STARTING_NPC_COUNT // 2, center[1]))
            for i in range(STARTING_NPC_COUNT)
        ]
        self.selected_npc: NPC | None = None

        initial_nests = create_initial_nests(
            self.grid.width, self.grid.height, NEST_INITIAL_COUNT, random.Random()
        )
        self.nest_manager = NestManager(self.grid.width, self.grid.height, initial_nests)
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
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_SPACE:
                    self.paused = not self.paused
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.handle_click(event.pos)

    def handle_click(self, screen_pos: tuple[int, int]) -> None:
        world_x = screen_pos[0] + self.camera.x
        world_y = screen_pos[1] + self.camera.y

        clicked_npc = self._npc_at_world_pos(world_x, world_y)
        if clicked_npc is not None:
            self.selected_npc = clicked_npc
            return

        gx, gy = tile_at(world_x, world_y)
        if not self.grid.in_bounds(gx, gy):
            return
        if self.selected_npc is None or not self.grid.get(gx, gy).claimed:
            return

        start = tile_at(self.selected_npc.x, self.selected_npc.y)
        path = find_path(
            lambda x, y: self.grid.get(x, y).claimed,
            self.grid.width,
            self.grid.height,
            start,
            (gx, gy),
        )
        if path:
            self.selected_npc.set_path(path)

    def _npc_at_world_pos(self, wx: float, wy: float) -> NPC | None:
        for npc in self.npcs:
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
            for npc in self.npcs:
                npc.update(dt)

            for tile in self.nest_manager.update(dt, self.cycle.round_number, self.cycle.phase):
                self.monsters.append(spawn_monster(tile, self.grid))
            for monster in self.monsters:
                monster.update(dt)

            resolve_combat(self.npcs, self.monsters)
            if self.selected_npc is not None and self.selected_npc.is_dead:
                self.selected_npc = None

    def render(self) -> None:
        self.screen.fill(COLOR_BG)
        self.render_grid()
        self.render_nests()
        self.render_npcs()
        self.render_monsters()
        self.render_hud()
        pygame.display.flip()

    def render_npcs(self) -> None:
        for npc in self.npcs:
            screen_x = int(npc.x - self.camera.x)
            screen_y = int(npc.y - self.camera.y)
            pygame.draw.circle(self.screen, COLOR_NPC, (screen_x, screen_y), NPC_RADIUS)
            if npc is self.selected_npc:
                pygame.draw.circle(self.screen, COLOR_NPC_SELECTED, (screen_x, screen_y), NPC_RADIUS, 2)

    def render_monsters(self) -> None:
        for monster in self.monsters:
            screen_x = int(monster.x - self.camera.x)
            screen_y = int(monster.y - self.camera.y)
            pygame.draw.circle(self.screen, COLOR_MONSTER, (screen_x, screen_y), NPC_RADIUS)

    def render_nests(self) -> None:
        for nest in self.nest_manager.nests:
            if not self.grid.get(nest.x, nest.y).revealed:
                continue
            screen_x = nest.x * TILE_SIZE - self.camera.x
            screen_y = nest.y * TILE_SIZE - self.camera.y
            rect = pygame.Rect(screen_x, screen_y, TILE_SIZE, TILE_SIZE)
            pygame.draw.rect(self.screen, COLOR_NEST, rect)

    def render_grid(self) -> None:
        cam_x, cam_y = self.camera.x, self.camera.y
        start_col = cam_x // TILE_SIZE
        start_row = cam_y // TILE_SIZE

        for row in range(start_row, min(self.grid.height, start_row + VIEWPORT_TILES_Y + 2)):
            for col in range(start_col, min(self.grid.width, start_col + VIEWPORT_TILES_X + 2)):
                tile = self.grid.get(col, row)
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
            "PAUSED" if self.paused else "",
        ]
        y = 8
        for i, text in enumerate(lines):
            if not text:
                continue
            color = banner_color if i == 0 else COLOR_TEXT
            surf = self.font.render(text, True, color)
            self.screen.blit(surf, (8, y))
            y += surf.get_height() + 4
