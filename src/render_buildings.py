import pygame

from extensions import register_overlay
from constants import TILE_SIZE, COLOR_WALL, COLOR_TOWER, COLOR_ANIMAL_PEN


def draw_buildings(surface: pygame.Surface, world, camera) -> None:
    for building in world.buildings:
        screen_x = building.x * TILE_SIZE - int(camera.x)
        screen_y = building.y * TILE_SIZE - int(camera.y)
        if building.type == "Wall":
            color = COLOR_WALL
        elif building.type == "Tower":
            color = COLOR_TOWER
        elif building.type == "AnimalPen":
            color = COLOR_ANIMAL_PEN
        else:
            color = COLOR_WALL
        rect = pygame.Rect(screen_x, screen_y, TILE_SIZE, TILE_SIZE)
        pygame.draw.rect(surface, color, rect)


register_overlay(draw_buildings)

