from __future__ import annotations

import math
import pygame

from constants import TILE_SIZE

_COLOR_VOID = (16, 14, 24)
_COLOR_MIST_SMOKE = (72, 68, 92)
_COLOR_MIST_SILVER = (175, 190, 218)
_COLOR_MIST_WHITE = (230, 240, 255)
_COLOR_MIST_CORE = (250, 252, 255)


def render_fog_tile(
    surface: pygame.Surface,
    rect: pygame.Rect,
    col: int,
    row: int,
    time_s: float,
    has_revealed_neighbor: bool = False,
) -> None:
    """Renders a dynamic, procedural drifting fog tile with rolling white vapor mist waves,
    swirling ethereal clouds, and puffy scalloped paper cloud borders on frontier edges."""
    # 1. Base Dark Ground Void
    pygame.draw.rect(surface, _COLOR_VOID, rect)

    # 2. Multi-Layer Drifting White Vapor Waves
    t = time_s
    w1 = math.sin(col * 0.55 + t * 0.65) * math.cos(row * 0.55 - t * 0.45)
    w2 = math.sin((col + row) * 0.38 - t * 0.90)

    density = (w1 + w2 + 2.0) / 4.0  # Normalized 0.0 to 1.0

    fog_surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)

    # Deep smoke mist foundation
    alpha1 = int(110 + 75 * density)
    pygame.draw.circle(
        fog_surf,
        (_COLOR_MIST_SMOKE[0], _COLOR_MIST_SMOKE[1], _COLOR_MIST_SMOKE[2], alpha1),
        (TILE_SIZE // 2 + int(w1 * 5), TILE_SIZE // 2 + int(w2 * 5)),
        TILE_SIZE // 2 + 6,
    )

    # Rolling silver-white vapor cloud
    if density > 0.35:
        alpha2 = int(90 + 110 * (density - 0.35) / 0.65)
        offset_x = int(math.sin(t * 1.1 + col * 0.8) * 6.0)
        offset_y = int(math.cos(t * 0.95 + row * 0.8) * 6.0)
        pygame.draw.ellipse(
            fog_surf,
            (_COLOR_MIST_SILVER[0], _COLOR_MIST_SILVER[1], _COLOR_MIST_SILVER[2], alpha2),
            pygame.Rect(3 + offset_x, 3 + offset_y, TILE_SIZE - 6, TILE_SIZE - 6),
        )

    # Pure white ethereal swirling mist wisps
    if density > 0.55:
        alpha3 = int(120 + 115 * (density - 0.55) / 0.45)
        wisp_cx = TILE_SIZE // 2 + int(w1 * 8)
        wisp_cy = TILE_SIZE // 2 + int(w2 * 8)
        pygame.draw.circle(
            fog_surf,
            (_COLOR_MIST_WHITE[0], _COLOR_MIST_WHITE[1], _COLOR_MIST_WHITE[2], alpha3),
            (wisp_cx, wisp_cy),
            TILE_SIZE // 3,
        )

    # Glowing bright white cloud core
    if density > 0.78:
        alpha4 = int(140 + 115 * (density - 0.78) / 0.22)
        pygame.draw.circle(
            fog_surf,
            (_COLOR_MIST_CORE[0], _COLOR_MIST_CORE[1], _COLOR_MIST_CORE[2], alpha4),
            (TILE_SIZE // 2, TILE_SIZE // 2),
            max(1, TILE_SIZE // 5),
        )

    # 3. Puffy White Scalloped Paper Cloud Border on Frontier Edges
    if has_revealed_neighbor:
        puff_pulse = math.sin(t * 2.2 + col + row) * 2.0
        puff_r = int(11 + puff_pulse)
        # Cloud base and puffy white body
        for px, py in [(0, TILE_SIZE // 2), (TILE_SIZE, TILE_SIZE // 2), (TILE_SIZE // 2, 0), (TILE_SIZE // 2, TILE_SIZE)]:
            pygame.draw.circle(fog_surf, (190, 205, 230, 180), (px, py), puff_r + 2)
            pygame.draw.circle(fog_surf, (240, 246, 255, 235), (px, py), puff_r)
            pygame.draw.circle(fog_surf, (255, 255, 255, 250), (px, py - 1), max(1, puff_r - 3))

    surface.blit(fog_surf, rect.topleft)
