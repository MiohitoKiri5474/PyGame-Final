import pygame

from constants import (
    COLOR_ANIMAL_PEN,
    COLOR_FARMLAND,
    COLOR_FARMLAND_READY,
    COLOR_HOUSE,
    COLOR_TOWER,
    COLOR_UNKNOWN_BUILDING,
    COLOR_WALL,
    TILE_SIZE,
)
from extensions import register_overlay

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


def draw_buildings(surface: pygame.Surface, world, camera) -> None:
    for building in world.buildings:
        screen_x = building.x * TILE_SIZE - int(camera.x)
        screen_y = building.y * TILE_SIZE - int(camera.y)
        rect = pygame.Rect(screen_x, screen_y, TILE_SIZE, TILE_SIZE)
        pygame.draw.rect(surface, _building_color(building), rect)


register_overlay(draw_buildings)
