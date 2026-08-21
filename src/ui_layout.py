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

import text_wrap
from constants import COLOR_BG, COLOR_TEXT, WINDOW_HEIGHT, WINDOW_WIDTH
from sprites import menu_button_sprite

BUTTON_WIDTH = 320  # wide enough to read as deliberate, not a leftover default-sized control
BUTTON_HEIGHT = 56
BUTTON_GAP = 12  # vertical gap between stacked rows - capped by the WINDOW_HEIGHT budget below (see the assert)
BUTTON_GAP_HORIZONTAL = 24  # gap between side-by-side buttons (ConfirmOverwriteDialog's Yes/No) - not height-budget-limited, so free to be wider
ROW_HEIGHT = BUTTON_HEIGHT + BUTTON_GAP

BUTTON_BG = (60, 64, 80)
BUTTON_BORDER = (140, 150, 180)

_SCREEN_TITLE_Y = WINDOW_HEIGHT // 3
_FRAME_MARGIN = 24
_TITLE_CLEARANCE = 30  # gap between the screen title text and the first button row
_TITLE_MAX_WIDTH = WINDOW_WIDTH - 160  # wrap width for render_screen_title, margin each side

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


# The 3 button-bar crops aren't vertically symmetric within their own
# bounding box - slot 1's banner flourish hangs down-left, slot 3's hangs
# down-right, pulling each crop's *geometric* center below the plain bar's
# own center (slot 2 is nearly symmetric, just a small vine-corner
# imbalance). Measured directly from the asset: how far below the crop's
# geometric center the bar's own center actually sits, as a fraction of
# the crop's height. Centering the raw crop on `rect` (as if this were 0
# for every slot) left slot 1's label rendering visibly high above the
# bar's middle - this corrects for it so the label always lands on the
# bar's true center regardless of which slot's flourish is heavier.
_BUTTON_SLOT_OFFSETS = {
    1: 28.5 / 331,   # top row: banner flourish on top-left
    2: 11.0 / 298,   # middle row: symmetric plain stone
    3: 5.0 / 298,    # bottom row: banner flourish on bottom-right
}


def render_button(
    surface: pygame.Surface, font: pygame.font.Font, rect: pygame.Rect, label: str, slot: int = 2
) -> None:
    """`slot` (1/2/3) picks which of the 3 painted button-bar crops to draw
    - an ordered set of buttons (title screen's Start/Continue/Settings)
    uses 1/2/3 in order; any other, standalone button just uses 2 (the
    plain symmetric one). The art is drawn with its visual stone center
    strictly aligned with `rect.center`, ensuring button text is 100%
    dead-centered vertically and horizontally. Falls back to the old flat
    rect+border look if the art isn't available."""
    art = menu_button_sprite(slot, rect.width + 32, rect.height + 24)
    if art is not None:
        y_offset = round(_BUTTON_SLOT_OFFSETS.get(slot, 0.0) * art.get_height())
        surface.blit(art, art.get_rect(center=(rect.centerx, rect.centery - y_offset)))
    else:
        pygame.draw.rect(surface, BUTTON_BG, rect)
        pygame.draw.rect(surface, BUTTON_BORDER, rect, 2)
    label_surface = font.render(label, True, COLOR_TEXT)
    surface.blit(label_surface, label_surface.get_rect(center=rect.center))


def render_screen_title(surface: pygame.Surface, font: pygame.font.Font, text: str) -> None:
    """The heading text every menu-style screen shows above its buttons -
    wrapped across multiple centered lines if it doesn't fit on one at
    `font`'s size. Pass a larger font (Game.menu_big_font) than the button
    labels use, for a heading that actually reads as one. Doesn't apply
    algorithmic bold: `font` is expected to already be a bold-weight face
    (the bundled LoRes9OTWide-Bold) - stacking pygame's synthetic bold on
    top of an already-bold pixel font visibly mushes its edges together
    (confirmed by rendering both ways and comparing)."""
    lines = text_wrap.wrap(text, font, _TITLE_MAX_WIDTH)
    line_h = font.get_linesize()
    top = _SCREEN_TITLE_Y - (len(lines) * line_h) // 2
    for i, line in enumerate(lines):
        line_surface = font.render(line, True, COLOR_TEXT)
        surface.blit(line_surface, line_surface.get_rect(centerx=WINDOW_WIDTH // 2, top=top + i * line_h))


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
