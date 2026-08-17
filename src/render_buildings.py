import pygame

from extensions import register_overlay
from constants import TILE_SIZE, COLOR_WALL, COLOR_TOWER
from sprites import building_sprite


def draw_buildings(surface: pygame.Surface, world, camera) -> None:
    for building in world.buildings:
        screen_x = building.x * TILE_SIZE - int(camera.x)
        screen_y = building.y * TILE_SIZE - int(camera.y)
        rect = pygame.Rect(screen_x, screen_y, TILE_SIZE, TILE_SIZE)

        sprite = building_sprite(building.type)
        if sprite is not None:
            surface.blit(sprite, sprite.get_rect(center=rect.center))
        else:
            color = COLOR_WALL if building.type == "Wall" else COLOR_TOWER
            pygame.draw.rect(surface, color, rect)


register_overlay(draw_buildings)
