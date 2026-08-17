import pygame

from constants import (
    WINDOW_WIDTH,
    WINDOW_HEIGHT,
    FPS,
    TILE_SIZE,
    VIEWPORT_TILES_X,
    VIEWPORT_TILES_Y,
    COLOR_BG,
    COLOR_FOG,
    COLOR_UNCLAIMED,
    COLOR_CLAIMED_EMPTY,
    COLOR_RESOURCE,
    COLOR_GRID_LINE,
    COLOR_TEXT,
    COLOR_DAY_BANNER,
    COLOR_NIGHT_BANNER,
)
from grid import Grid
from camera import Camera
from day_night import DayNightCycle, DAY


class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Colony Defense (WIP)")
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(None, 24)

        self.grid = Grid()
        self.camera = Camera()
        self.cycle = DayNightCycle()
        self.paused = False
        self.running = True

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

    def update(self, dt: float) -> None:
        keys = pygame.key.get_pressed()
        dx = (keys[pygame.K_RIGHT] or keys[pygame.K_d]) - (keys[pygame.K_LEFT] or keys[pygame.K_a])
        dy = (keys[pygame.K_DOWN] or keys[pygame.K_s]) - (keys[pygame.K_UP] or keys[pygame.K_w])
        self.camera.pan(dx, dy, dt)  # camera pans even while paused

        if not self.paused:
            self.cycle.update(dt)

    def render(self) -> None:
        self.screen.fill(COLOR_BG)
        self.render_grid()
        self.render_hud()
        pygame.display.flip()

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
