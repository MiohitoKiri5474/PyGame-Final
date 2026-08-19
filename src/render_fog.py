from __future__ import annotations

import math
import pygame

from constants import TILE_SIZE

_COLOR_VOID = (14, 11, 24)
_COLOR_MIST_DEEP = (38, 20, 56)
_COLOR_MIST_MID = (56, 30, 84)
_COLOR_MIST_LIGHT = (85, 48, 125)


def render_fog_tile(
    surface: pygame.Surface,
    rect: pygame.Rect,
    col: int,
    row: int,
    time_s: float,
    has_revealed_neighbor: bool = False,
) -> None:
    """Renders a dynamic, procedural drifting fog tile with swirling mist waves,
    glowing purple cloud layers, and scalloped paper cloud borders on frontier edges."""
    # 1. Base Cosmic Void
    pygame.draw.rect(surface, _COLOR_VOID, rect)

    # 2. Dual-Layer Drifting Mist Waves
    # Continuous flowing mist calculations
    t = time_s
    w1 = math.sin(col * 0.55 + t * 0.6) * math.cos(row * 0.55 - t * 0.45)
    w2 = math.sin((col + row) * 0.40 - t * 0.85)

    density = (w1 + w2 + 2.0) / 4.0  # Normalized 0.0 to 1.0

    # Draw swirling mist clouds
    fog_surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)

    # Deep purple mist foundation
    alpha1 = int(120 + 90 * density)
    pygame.draw.circle(
        fog_surf,
        (_COLOR_MIST_DEEP[0], _COLOR_MIST_DEEP[1], _COLOR_MIST_DEEP[2], alpha1),
        (TILE_SIZE // 2 + int(w1 * 6), TILE_SIZE // 2 + int(w2 * 6)),
        TILE_SIZE // 2 + 6,
    )

    # Lighter swirling mist wisps
    if density > 0.45:
        alpha2 = int(70 + 110 * (density - 0.45) / 0.55)
        offset_x = int(math.sin(t * 1.2 + col) * 5.0)
        offset_y = int(math.cos(t * 1.0 + row) * 5.0)
        pygame.draw.ellipse(
            fog_surf,
            (_COLOR_MIST_MID[0], _COLOR_MIST_MID[1], _COLOR_MIST_MID[2], alpha2),
            pygame.Rect(4 + offset_x, 4 + offset_y, TILE_SIZE - 8, TILE_SIZE - 8),
        )

    # High-density glowing mist core
    if density > 0.72:
        alpha3 = int(60 + 80 * (density - 0.72) / 0.28)
        pygame.draw.circle(
            fog_surf,
            (_COLOR_MIST_LIGHT[0], _COLOR_MIST_LIGHT[1], _COLOR_MIST_LIGHT[2], alpha3),
            (TILE_SIZE // 2, TILE_SIZE // 2),
            TILE_SIZE // 4,
        )

    # 3. Paper Mario Scalloped Cloud Border on Frontier Edges
    if has_revealed_neighbor:
        # Puffy billowy cloud scalloping around border
        puff_pulse = math.sin(t * 2.0 + col + row) * 2.0
        puff_r = int(10 + puff_pulse)
        puff_col = (50, 32, 74, 210)
        pygame.draw.circle(fog_surf, puff_col, (0, TILE_SIZE // 2), puff_r)
        pygame.draw.circle(fog_surf, puff_col, (TILE_SIZE, TILE_SIZE // 2), puff_r)
        pygame.draw.circle(fog_surf, puff_col, (TILE_SIZE // 2, 0), puff_r)
        pygame.draw.circle(fog_surf, puff_col, (TILE_SIZE // 2, TILE_SIZE), puff_r)

    surface.blit(fog_surf, rect.topleft)
