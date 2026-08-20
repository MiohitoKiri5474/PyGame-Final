import math
import time

import pygame

from constants import (
    COLOR_ANIMAL_PEN,
    COLOR_FARMLAND,
    COLOR_FARMLAND_READY,
    COLOR_HOUSE,
    COLOR_TOWER,
    COLOR_UNKNOWN_BUILDING,
    COLOR_WALL,
    FARMLAND_GROW_SECONDS,
    TILE_SIZE,
)
from extensions import register_overlay
from sprites import building_sprite, map_resource_sprite

_COLOR_BY_TYPE = {
    "Wall": COLOR_WALL, "Tower": COLOR_TOWER, "House": COLOR_HOUSE, "AnimalPen": COLOR_ANIMAL_PEN,
}


def _building_color(building) -> tuple[int, int, int]:
    if building.type == "Farmland":
        return COLOR_FARMLAND_READY if building.ready else COLOR_FARMLAND
    # Unmapped types render magenta, not a plausible-looking wrong color - a
    # future building type left out of _COLOR_BY_TYPE fails loudly on screen
    # instead of silently misrendering as an existing type (e.g. Tower-blue).
    return _COLOR_BY_TYPE.get(building.type, COLOR_UNKNOWN_BUILDING)


def draw_single_building(surface: pygame.Surface, building, camera) -> None:
    screen_x = building.x * TILE_SIZE - int(camera.x)
    screen_y = building.y * TILE_SIZE - int(camera.y)
    rect = pygame.Rect(screen_x, screen_y, TILE_SIZE, TILE_SIZE)

    sprite = building_sprite(building)
    if sprite is not None:
        if building.type == "Farmland":
            # 1. Base cultivated soil layer
            surface.blit(sprite, rect.topleft)

            if building.ready:
                # 2. 2.5D Ready Harvest: Golden wheat stalks standing on the soil
                crop_sprite = map_resource_sprite("crop")
                if crop_sprite is not None:
                    c_rect = crop_sprite.get_rect(midbottom=(rect.centerx, rect.bottom - 1))
                    surface.blit(crop_sprite, c_rect)

                # Gentle golden ready sparkle
                t_pulse = time.monotonic() * 4.0
                sparkle_alpha = int(180 + 75 * math.sin(t_pulse))
                sparkle_surf = pygame.Surface((6, 6), pygame.SRCALPHA)
                pygame.draw.circle(sparkle_surf, (255, 255, 200, sparkle_alpha), (3, 3), 2)
                surface.blit(sparkle_surf, (rect.right - 8, rect.top + 4))
            else:
                # 3. Growing State: Sprout progression & growth progress bar
                timer = getattr(building, "growth_timer", 0.0)
                prog = min(1.0, max(0.0, timer / FARMLAND_GROW_SECONDS))
                if prog > 0.15:
                    sprout_h = 2 if prog < 0.50 else 4
                    sprout_col = (100, 210, 70) if prog < 0.50 else (130, 230, 80)
                    for ox, oy in [(10, 14), (20, 10), (30, 16), (15, 26), (28, 24)]:
                        pygame.draw.line(surface, (80, 180, 50), (rect.x + ox, rect.y + oy + sprout_h), (rect.x + ox, rect.y + oy - sprout_h), 2)
                        pygame.draw.circle(surface, sprout_col, (rect.x + ox, rect.y + oy - sprout_h), 2)

                # Growth progress bar at bottom of farmland
                if 0.0 < prog < 1.0:
                    bar_w = TILE_SIZE - 8
                    bar_h = 3
                    bar_rect = pygame.Rect(rect.x + 4, rect.bottom - 5, bar_w, bar_h)
                    pygame.draw.rect(surface, (30, 40, 30), bar_rect, border_radius=2)
                    fill_w = max(1, int(bar_w * prog))
                    pygame.draw.rect(surface, (100, 225, 80), pygame.Rect(bar_rect.x, bar_rect.y, fill_w, bar_h), border_radius=2)
        else:
            # 2.5D Standing Structure: Soft ground shadow at the base
            sw = max(16, int(sprite.get_width() * 0.80))
            sh = max(6, int(TILE_SIZE * 0.35))
            shadow_surf = pygame.Surface((sw, sh), pygame.SRCALPHA)
            pygame.draw.ellipse(shadow_surf, (0, 0, 0, 85), (0, 0, sw, sh))
            surface.blit(shadow_surf, (rect.centerx - sw // 2, rect.bottom - sh // 2 - 2))

            # 2.5D Anchor: Base sits at tile bottom, top towers upward
            b_rect = sprite.get_rect(midbottom=(rect.centerx, rect.bottom))
            surface.blit(sprite, b_rect)
    else:
        pygame.draw.rect(surface, _building_color(building), rect)


def draw_buildings(surface: pygame.Surface, world, camera) -> None:
    # Sort buildings north-to-south (Y-order) so structures stack correctly
    sorted_buildings = sorted(world.buildings, key=lambda b: (b.y, b.x))
    for building in sorted_buildings:
        draw_single_building(surface, building, camera)


register_overlay(draw_buildings)
