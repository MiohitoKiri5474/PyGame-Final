from __future__ import annotations

import math
import pygame

from constants import (
    TILE_SIZE,
    WINDOW_WIDTH,
    WINDOW_HEIGHT,
    COLOR_FOG,
)
from coords import tile_at
from sprites import cloud_sprite, fog_sprite

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
    """Renders large, organic, continuous clouds and mist floating smoothly across
    unexplored regions of the map (not confined to individual grid squares)."""
    cam_x, cam_y = camera.x, camera.y

    # Calculate world bounds visible on screen plus generous margin for large clouds
    margin = 160
    min_wx = max(0, int(cam_x - margin))
    max_wx = min(grid.width * TILE_SIZE, int(cam_x + WINDOW_WIDTH + margin))
    min_wy = max(0, int(cam_y - margin))
    max_wy = min(grid.height * TILE_SIZE, int(cam_y + WINDOW_HEIGHT + margin))

    # Dense cloud cluster spacing across the world for rich seamless coverage
    step_x = 44
    step_y = 38

    start_cx = min_wx // step_x
    end_cx = (max_wx // step_x) + 1
    start_cy = min_wy // step_y
    end_cy = (max_wy // step_y) + 1

    for cy_idx in range(start_cy, end_cy):
        for cx_idx in range(start_cx, end_cx):
            # Unique deterministic seed for this cloud slot
            seed = (cx_idx * 73856093 ^ cy_idx * 19349663) % 1000

            # Organic floating motion: drifting right and bobbing vertically
            drift_speed = 9.0 + (seed % 5) * 1.5
            drift_x = (time_s * drift_speed + seed * 2.0) % (grid.width * TILE_SIZE + 200) - 100
            bob_y = math.sin(time_s * 1.0 + seed * 0.1) * 7.0 + math.cos(time_s * 0.6 + seed * 0.2) * 5.0

            # Base anchor in world coordinates with drifting sway
            wx = cx_idx * step_x + math.sin(cy_idx * 1.9 + seed) * 18.0 + (time_s * 7.0) % 120
            wy = cy_idx * step_y + math.cos(cx_idx * 1.6 + seed) * 14.0 + bob_y

            # Check if this cloud position is within world bounds
            gtx, gty = tile_at(wx, wy)
            if not (0 <= gtx < grid.width and 0 <= gty < grid.height):
                continue

            tile = grid.get(gtx, gty)

            # If the center tile is claimed and revealed, check if any nearby tiles are unrevealed
            if tile.revealed:
                is_near_fog = False
                for dtx, dty in [(-2, 0), (2, 0), (0, -2), (0, 2), (-1, -1), (1, 1), (-1, 1), (1, -1)]:
                    nx, ny = gtx + dtx, gty + dty
                    if 0 <= nx < grid.width and 0 <= ny < grid.height and not grid.get(nx, ny).revealed:
                        is_near_fog = True
                        break
                if not is_near_fog:
                    continue  # Skip clouds completely inside deep revealed colony
                cloud_alpha = 175  # Soft feathering at frontier edge
            else:
                cloud_alpha = 245 + (seed % 10)  # Dense, thick, solid cloud coverage over unexplored lands

            # Select cloud variant (0..14) and scale to large thick cloud sizes
            cloud_variant = seed % 15
            cloud_width = 110 + (seed % 8) * 18  # 110px to 236px for plush dense overlap
            cloud_img = cloud_sprite(index=cloud_variant, width=cloud_width)

            if cloud_img is None:
                continue

            # Screen coordinates
            sx = int(wx - cam_x)
            sy = int(wy - cam_y)

            # Render thick floating cloud
            c_surf = cloud_img.copy()
            if cloud_alpha < 255:
                c_surf.fill((255, 255, 255, cloud_alpha), special_flags=pygame.BLEND_RGBA_MULT)

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
