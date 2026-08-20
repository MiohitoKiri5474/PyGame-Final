"""Shared button-row layout for the game's menu-style screens (title,
pause menu, settings, overwrite-confirm) - primitive shapes/text only.

Screens reachable directly from PLAYING or app launch (title, pause menu)
share FIRST_LEVEL_TOP; screens reachable as a second click from one of
those (overwrite-confirm, settings) share SECOND_LEVEL_TOP instead. Two
screens sharing a level are never adjacent in the state machine (a click
can't jump directly from one to the other), so they're safe to reuse the
same rows - but a screen and anything it can transition into by one click
DO need distinct rows, or a same-position double-click can land a click
meant for one screen on the other. (This is exactly the class of bug that
shipped once already between the title screen's Start button and the
overwrite-confirm dialog's Yes/No buttons - this module exists so it
can't quietly happen again as more screens get added.)
"""

from __future__ import annotations

import pygame

from constants import COLOR_BG, COLOR_TEXT, WINDOW_HEIGHT, WINDOW_WIDTH
from sprites import menu_button_sprite

BUTTON_WIDTH = 320  # wide enough to read as deliberate, not a leftover default-sized control
BUTTON_HEIGHT = 56
BUTTON_GAP = 8
ROW_HEIGHT = BUTTON_HEIGHT + BUTTON_GAP

BUTTON_BG = (60, 64, 80)
BUTTON_BORDER = (140, 150, 180)

_SCREEN_TITLE_Y = WINDOW_HEIGHT // 3
_FRAME_MARGIN = 24
_TITLE_CLEARANCE = 40  # gap between the screen title text and the first button row

# Tallest screen at each level, in rows - keep these equal to the actual
# max (TitleScreen uses 3, PauseMenu uses 4; SettingsScreen uses 3, only
# ConfirmOverwriteDialog uses the second level otherwise, as one
# horizontal row). Bump the relevant constant if a screen grows past this,
# the assert below catches an overflow immediately instead of silently
# rendering an unclickable off-screen button.
FIRST_LEVEL_ROWS = 4
SECOND_LEVEL_ROWS = 3

FIRST_LEVEL_TOP = _SCREEN_TITLE_Y + _TITLE_CLEARANCE
SECOND_LEVEL_TOP = FIRST_LEVEL_TOP + FIRST_LEVEL_ROWS * ROW_HEIGHT

_content_bottom = SECOND_LEVEL_TOP + (SECOND_LEVEL_ROWS - 1) * ROW_HEIGHT + BUTTON_HEIGHT
assert _content_bottom <= WINDOW_HEIGHT - _FRAME_MARGIN - BUTTON_GAP, (
    "menu content overflows the window - grow WINDOW_HEIGHT or shrink "
    "ROW_HEIGHT/FIRST_LEVEL_ROWS/SECOND_LEVEL_ROWS"
)


def stack_rect(top: int, index: int) -> pygame.Rect:
    """A single-column button rect, `index` rows below `top`."""
    return pygame.Rect(
        (WINDOW_WIDTH - BUTTON_WIDTH) // 2, top + index * ROW_HEIGHT, BUTTON_WIDTH, BUTTON_HEIGHT
    )


def hit_test(pos: tuple[int, int], rect_labels: list[tuple[pygame.Rect, str]]) -> str | None:
    for rect, label in rect_labels:
        if rect.collidepoint(pos):
            return label
    return None


def render_button(
    surface: pygame.Surface, font: pygame.font.Font, rect: pygame.Rect, label: str, slot: int = 2
) -> None:
    """`slot` (1/2/3) picks which of the 3 painted button-bar crops to draw
    - an ordered set of buttons (title screen's Start/Continue/Settings)
    uses 1/2/3 in order; any other, standalone button just uses 2 (the
    plain symmetric one). The art is drawn a little larger than `rect` for
    breathing room around its ornate border, but `rect` itself - and so the
    actual click hit-box - is unchanged. Falls back to the old flat
    rect+border look if the art isn't available."""
    art = menu_button_sprite(slot, rect.width + 32, rect.height + 24)
    if art is not None:
        surface.blit(art, art.get_rect(center=rect.center))
    else:
        pygame.draw.rect(surface, BUTTON_BG, rect)
        pygame.draw.rect(surface, BUTTON_BORDER, rect, 2)
    label_surface = font.render(label, True, COLOR_TEXT)
    surface.blit(label_surface, label_surface.get_rect(center=rect.center))


def render_screen_title(surface: pygame.Surface, font: pygame.font.Font, text: str) -> None:
    """The heading text every menu-style screen shows above its buttons."""
    title_surface = font.render(text, True, COLOR_TEXT)
    surface.blit(title_surface, title_surface.get_rect(center=(WINDOW_WIDTH // 2, _SCREEN_TITLE_Y)))


def render_screen_frame(surface: pygame.Surface) -> None:
    """A simple border a fixed margin in from the screen edges, so a menu
    screen reads as one deliberately-framed composition instead of a few
    small buttons floating in an otherwise-empty window. Fallback look for
    render_screen_background() when its painted art isn't available."""
    frame = pygame.Rect(
        _FRAME_MARGIN, _FRAME_MARGIN, WINDOW_WIDTH - 2 * _FRAME_MARGIN, WINDOW_HEIGHT - 2 * _FRAME_MARGIN
    )
    pygame.draw.rect(surface, BUTTON_BORDER, frame, 2)


def render_screen_background(surface: pygame.Surface, image: pygame.Surface | None) -> None:
    """Full-window painted backdrop for a menu-style screen, or the old
    flat-color-plus-border look if `image` (from sprites.py) isn't
    available - screens call this in place of render_screen_frame()."""
    if image is not None:
        surface.blit(image, (0, 0))
    else:
        surface.fill(COLOR_BG)
        render_screen_frame(surface)
