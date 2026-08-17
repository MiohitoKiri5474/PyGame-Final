import pygame

from constants import (
    WINDOW_WIDTH,
    WINDOW_HEIGHT,
    FPS,
    TILE_SIZE,
    GRID_WIDTH,
    GRID_HEIGHT,
    VIEWPORT_TILES_X,
    VIEWPORT_TILES_Y,
    NPC_MAX_HUNGER,
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
    COLOR_HUNGER_BAR,
    COLOR_BAR_BG,
)
from grid import Grid
from camera import Camera
from day_night import DayNightCycle, DAY
from npc import NPC


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

        # Spawn 3 starting NPCs near the centre of the claimed area
        self.npcs: list[NPC] = []
        cx = GRID_WIDTH // 2
        cy = GRID_HEIGHT // 2
        offsets = [(-1, 0), (0, 0), (1, 0)]  # spread horizontally
        for ox, oy in offsets:
            px = (cx + ox) * TILE_SIZE + TILE_SIZE // 2
            py = (cy + oy) * TILE_SIZE + TILE_SIZE // 2
            self.npcs.append(NPC(float(px), float(py)))

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
            for npc in self.npcs:
                npc.update(dt)
            # Remove dead NPCs (starvation or future combat)
            self.npcs = [n for n in self.npcs if n.alive]

    def render(self) -> None:
        self.screen.fill(COLOR_BG)
        self.render_grid()
        self.render_npcs()
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

    # ------------------------------------------------------------------
    # NPC rendering
    # ------------------------------------------------------------------

    def render_npcs(self) -> None:
        cam_x, cam_y = self.camera.x, self.camera.y
        npc_radius = TILE_SIZE // 3
        bar_w = TILE_SIZE - 4
        bar_h = 4

        for npc in self.npcs:
            sx = int(npc.x - cam_x)
            sy = int(npc.y - cam_y)

            # Body
            pygame.draw.circle(self.screen, COLOR_NPC, (sx, sy), npc_radius)

            # Hunger bar (above the NPC)
            bar_x = sx - bar_w // 2
            bar_y = sy - npc_radius - bar_h - 4
            hunger_ratio = npc.hunger / NPC_MAX_HUNGER
            # Background
            pygame.draw.rect(self.screen, COLOR_BAR_BG,
                             pygame.Rect(bar_x, bar_y, bar_w, bar_h))
            # Fill
            fill_w = max(0, int(bar_w * hunger_ratio))
            if fill_w > 0:
                pygame.draw.rect(self.screen, COLOR_HUNGER_BAR,
                                 pygame.Rect(bar_x, bar_y, fill_w, bar_h))

    # ------------------------------------------------------------------
    # HUD
    # ------------------------------------------------------------------

    def render_hud(self) -> None:
        banner_color = COLOR_DAY_BANNER if self.cycle.phase == DAY else COLOR_NIGHT_BANNER
        lines = [
            f"Round {self.cycle.round_number} - {self.cycle.phase.upper()}  ({self.cycle.remaining():.0f}s)",
            f"NPCs alive: {len(self.npcs)}",
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
