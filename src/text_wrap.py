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


def wrap_groups(text: str, font: pygame.font.Font, max_width: int, sep: str = "   ") -> list[str]:
    """Like wrap(), but for hint bars built from `sep`-separated "[key]
    label" groups (e.g. "[Up/Down] select   [K/Esc] close") - treats each
    group as an atomic unit that's never split across lines, so a key never
    gets separated from its own label mid-line."""
    groups = [g for g in text.split(sep) if g]
    lines: list[str] = []
    current = ""
    for group in groups:
        candidate = f"{current}{sep}{group}" if current else group
        if current and font.size(candidate)[0] > max_width:
            lines.append(current)
            current = group
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines
