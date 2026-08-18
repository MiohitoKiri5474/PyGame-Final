import pygame

from extensions import register_overlay
from constants import TILE_SIZE, COLOR_WALL, COLOR_TOWER, COLOR_HOUSE, COLOR_UNKNOWN_BUILDING

_COLOR_BY_TYPE = {"Wall": COLOR_WALL, "Tower": COLOR_TOWER, "House": COLOR_HOUSE}


def draw_buildings(surface: pygame.Surface, world, camera) -> None:
    for building in world.buildings:
        screen_x = building.x * TILE_SIZE - int(camera.x)
        screen_y = building.y * TILE_SIZE - int(camera.y)
        # Unmapped types render magenta, not a plausible-looking wrong color -
        # a future building type left out of _COLOR_BY_TYPE fails loudly on
        # screen instead of silently misrendering as an existing type.
        color = _COLOR_BY_TYPE.get(building.type, COLOR_UNKNOWN_BUILDING)
        rect = pygame.Rect(screen_x, screen_y, TILE_SIZE, TILE_SIZE)
        pygame.draw.rect(surface, color, rect)


register_overlay(draw_buildings)
