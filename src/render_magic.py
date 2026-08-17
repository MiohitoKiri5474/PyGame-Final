import pygame

from extensions import register_overlay


def draw_magic_fx(surface: pygame.Surface, world, camera) -> None:
    spellbook = world.spellbook
    # flash_color is always co-assigned with flash_position/flash_timer in
    # Spellbook.trigger_flash (the only place any of the three are set) - no
    # separate None-check needed for a state that can't actually occur.
    if spellbook.flash_timer <= 0 or spellbook.flash_position is None:
        return
    x, y = spellbook.flash_position
    screen_x = int(x - camera.x)
    screen_y = int(y - camera.y)
    pygame.draw.circle(surface, spellbook.flash_color, (screen_x, screen_y), 20, 3)


register_overlay(draw_magic_fx)
