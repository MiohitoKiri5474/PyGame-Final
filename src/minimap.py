"""Small bottom-left overview map: the whole grid's fog/claimed state at a
glance, with a rectangle marking the camera's current viewport - answers
"which part of the explored area am I looking at right now". Display only,
no click-to-navigate (not asked for).

Sits directly above the build bar - `bottom` is the build bar's own outer
panel top (build_bar.BuildBar.panel_top()), so it never overlaps it however
tall the build bar's own description/tooltip layout ends up being.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from constants import GRID_HEIGHT, GRID_WIDTH, TILE_SIZE, VIEWPORT_TILES_X, VIEWPORT_TILES_Y

if TYPE_CHECKING:
    from camera import Camera
    from grid import Grid

_MARGIN = 10
_GAP_ABOVE_BUILD_BAR = 10
_WIDTH = 170  # matches the left column (top_bar.LEFT_W / magic_panel)
_HEIGHT = round(_WIDTH * GRID_HEIGHT / GRID_WIDTH)
_OUTER_PAD = 6

_OUTER_BG = (18, 20, 26)
_OUTER_BORDER = (60, 64, 76)
_FOG_COLOR = (28, 28, 36)
_UNCLAIMED_COLOR = (95, 82, 55)
_CLAIMED_COLOR = (70, 112, 50)
_VIEWPORT_COLOR = (255, 214, 100)


def outer_rect(build_bar_top: int) -> pygame.Rect:
    height = _HEIGHT + _OUTER_PAD * 2
    width = _WIDTH + _OUTER_PAD * 2
    bottom = build_bar_top - _GAP_ABOVE_BUILD_BAR
    return pygame.Rect(_MARGIN, bottom - height, width, height)


def render(surface: pygame.Surface, grid: "Grid", camera: "Camera", build_bar_top: int) -> None:
    outer = outer_rect(build_bar_top)
    pygame.draw.rect(surface, _OUTER_BG, outer, border_radius=8)
    pygame.draw.rect(surface, _OUTER_BORDER, outer, 2, border_radius=8)

    small = pygame.Surface((grid.width, grid.height))
    for y in range(grid.height):
        for x in range(grid.width):
            tile = grid.get(x, y)
            if not tile.revealed:
                color = _FOG_COLOR
            elif tile.claimed:
                color = _CLAIMED_COLOR
            else:
                color = _UNCLAIMED_COLOR
            small.set_at((x, y), color)

    map_pos = (outer.x + _OUTER_PAD, outer.y + _OUTER_PAD)
    scaled = pygame.transform.scale(small, (_WIDTH, _HEIGHT))
    surface.blit(scaled, map_pos)

    scale_x = _WIDTH / (grid.width * TILE_SIZE)
    scale_y = _HEIGHT / (grid.height * TILE_SIZE)
    viewport_rect = pygame.Rect(
        map_pos[0] + round(camera.x * scale_x),
        map_pos[1] + round(camera.y * scale_y),
        round(VIEWPORT_TILES_X * TILE_SIZE * scale_x),
        round(VIEWPORT_TILES_Y * TILE_SIZE * scale_y),
    )
    map_rect = pygame.Rect(map_pos, (_WIDTH, _HEIGHT))
    pygame.draw.rect(surface, _VIEWPORT_COLOR, viewport_rect.clip(map_rect), 2)
