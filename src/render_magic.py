import pygame

from constants import COLOR_LIGHTNING_FLASH
from extensions import register_overlay


def draw_magic_fx(surface: pygame.Surface, world, camera) -> None:
    spellbook = world.spellbook
    if spellbook.flash_timer <= 0 or spellbook.flash_position is None:
        return
    x, y = spellbook.flash_position
    screen_x = int(x - camera.x)
    screen_y = int(y - camera.y)
    pygame.draw.circle(surface, COLOR_LIGHTNING_FLASH, (screen_x, screen_y), 20, 3)


register_overlay(draw_magic_fx)
