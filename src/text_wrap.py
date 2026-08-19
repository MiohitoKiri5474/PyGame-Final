"""Shared greedy word-wrap for narrow HUD text - packs words onto a line
until the next one would overflow, then starts a new one. Used wherever a
fixed-width panel (magic_panel, top_bar's side info) needs to fit
variable-length text without measuring its own font metrics twice."""

from __future__ import annotations

import pygame


def wrap(text: str, font: pygame.font.Font, max_width: int) -> list[str]:
    words = text.split(" ")
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if current and font.size(candidate)[0] > max_width:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines
