from __future__ import annotations

import math
import pygame

from constants import (
    TILE_SIZE,
    WINDOW_WIDTH,
    WINDOW_HEIGHT,
)
from coords import tile_at
from sprites import cloud_sprite

_COLOR_VOID = (16, 14, 24)


def render_fog_base_tile(surface: pygame.Surface, rect: pygame.Rect) -> None:
    """Renders the dark ground void under unrevealed territory."""
    pygame.draw.rect(surface, _COLOR_VOID, rect)


def render_drifting_fog_layer(
    surface: pygame.Surface,
    grid,
    camera,
    time_s: float,
) -> None:
    """Renders high-performance, organic continuous clouds floating over unexplored
    wilderness, with reduced coverage on explorable borders to keep them clear and visible."""
    cam_x, cam_y = camera.x, camera.y

    # Calculate world bounds visible on screen plus margin for clouds
    margin = 140
    min_wx = max(0, int(cam_x - margin))
    max_wx = min(grid.width * TILE_SIZE, int(cam_x + WINDOW_WIDTH + margin))
    min_wy = max(0, int(cam_y - margin))
    max_wy = min(grid.height * TILE_SIZE, int(cam_y + WINDOW_HEIGHT + margin))

    # Balanced spacing for silky smooth 60 FPS performance and rich coverage
    step_x = 76
    step_y = 66

    start_cx = min_wx // step_x
    end_cx = (max_wx // step_x) + 1
    start_cy = min_wy // step_y
    end_cy = (max_wy // step_y) + 1

    for cy_idx in range(start_cy, end_cy):
        for cx_idx in range(start_cx, end_cx):
            # Unique deterministic seed for this cloud slot
            seed = (cx_idx * 73856093 ^ cy_idx * 19349663) % 1000

            # Floating motion: smooth horizontal drift and gentle vertical bobbing
            drift_speed = 8.0 + (seed % 4) * 1.5
            bob_y = math.sin(time_s * 0.9 + seed * 0.1) * 6.0 + math.cos(time_s * 0.5 + seed * 0.2) * 4.0

            # Base anchor in world coordinates
            wx = cx_idx * step_x + math.sin(cy_idx * 1.8 + seed) * 16.0 + (time_s * drift_speed) % 150
            wy = cy_idx * step_y + math.cos(cx_idx * 1.5 + seed) * 14.0 + bob_y

            # Check world bounds
            gtx, gty = tile_at(wx, wy)
            if not (0 <= gtx < grid.width and 0 <= gty < grid.height):
                continue

            tile = grid.get(gtx, gty)

            # Never spawn clouds over revealed colony territory
            if tile.revealed:
                continue

            # Check if this unexplored tile borders a revealed/explorable tile
            has_revealed_adj = False
            for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, 1), (-1, 1), (1, -1)):
                nx, ny = gtx + dx, gty + dy
                if 0 <= nx < grid.width and 0 <= ny < grid.height and grid.get(nx, ny).revealed:
                    has_revealed_adj = True
                    break

            if has_revealed_adj:
                # On the explorable frontier edge: abundant clouds with high transparency (very see-through)
                # so the terrain, trees, resources, and grid below remain clearly visible
                cloud_width = 100 + (seed % 5) * 16  # 100px - 164px
                cloud_alpha = 65 + (seed % 20)       # Alpha 65..84 (ethereal, highly translucent)
            else:
                # Deep unexplored interior: full thick dense cloud cover
                cloud_width = 140 + (seed % 6) * 18  # Large plush clouds (140px - 230px)
                cloud_alpha = 240


            # Screen coordinates
            sx = int(wx - cam_x)
            sy = int(wy - cam_y)

            # Fetch fully pre-cached, alpha-blended cloud sprite (0 per-frame allocations)
            cloud_variant = seed % 15
            c_surf = cloud_sprite(index=cloud_variant, width=cloud_width, alpha=cloud_alpha)
            surface.blit(c_surf, c_surf.get_rect(center=(sx, sy)))


def render_fog_tile(
    surface: pygame.Surface,
    rect: pygame.Rect,
    col: int,
    row: int,
    time_s: float,
    has_revealed_neighbor: bool = False,
) -> None:
    """Backward compatibility helper for single-tile invocations."""
    render_fog_base_tile(surface, rect)
