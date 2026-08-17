import pygame

from extensions import register_overlay
from constants import TILE_SIZE, COLOR_WALL, COLOR_TOWER


def draw_buildings(surface: pygame.Surface, world, camera) -> None:
    for building in world.buildings:
        screen_x = building.x * TILE_SIZE - int(camera.x)
        screen_y = building.y * TILE_SIZE - int(camera.y)
        color = COLOR_WALL if building.type == "Wall" else COLOR_TOWER
        rect = pygame.Rect(screen_x, screen_y, TILE_SIZE, TILE_SIZE)
        pygame.draw.rect(surface, color, rect)


register_overlay(draw_buildings)
