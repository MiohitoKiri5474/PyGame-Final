import pygame

from extensions import register_overlay
from constants import TILE_SIZE, COLOR_WALL, COLOR_TOWER, COLOR_FARMLAND, COLOR_FARMLAND_READY


def _building_color(building) -> tuple[int, int, int]:
    if building.type == "Wall":
        return COLOR_WALL
    if building.type == "Farmland":
        return COLOR_FARMLAND_READY if building.ready else COLOR_FARMLAND
    return COLOR_TOWER


def draw_buildings(surface: pygame.Surface, world, camera) -> None:
    for building in world.buildings:
        screen_x = building.x * TILE_SIZE - int(camera.x)
        screen_y = building.y * TILE_SIZE - int(camera.y)
        rect = pygame.Rect(screen_x, screen_y, TILE_SIZE, TILE_SIZE)
        pygame.draw.rect(surface, _building_color(building), rect)


register_overlay(draw_buildings)
