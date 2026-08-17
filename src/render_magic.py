import pygame

from extensions import register_overlay


def draw_magic_fx(surface: pygame.Surface, world, camera) -> None:
    for flash in world.spellbook.flashes:
        x, y = flash["position"]
        screen_x = int(x - camera.x)
        screen_y = int(y - camera.y)
        alpha = int(255 * (flash["timer"] / flash["duration"]))
        fx = pygame.Surface((48, 48), pygame.SRCALPHA)
        pygame.draw.circle(fx, (*flash["color"], alpha), (24, 24), 20, 3)
        surface.blit(fx, (screen_x - 24, screen_y - 24))


register_overlay(draw_magic_fx)
