"""Audio & Sound Effects Manager.

Loads sound effects from assets/sfx/ with lazy-caching and safe headless fallback
so tests and systems without audio devices continue working cleanly.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

import pygame

_SOUND_CACHE: dict[str, pygame.mixer.Sound | None] = {}
_SFX_DIR = Path(__file__).parent.parent / "assets" / "sfx"


def play_sfx(name: str, volume: float = 1.0) -> None:
    """Safely play a sound effect by name (e.g. 'chop', 'gather').
    Silently no-ops if pygame mixer is uninitialized or file is missing."""
    if not pygame.mixer.get_init():
        return

    if name not in _SOUND_CACHE:
        sound = None
        for ext in (".mp3", ".wav", ".ogg"):
            sound_path = _SFX_DIR / f"{name}{ext}"
            if sound_path.exists():
                try:
                    sound = pygame.mixer.Sound(str(sound_path))
                    break
                except (pygame.error, OSError):
                    sound = None
        _SOUND_CACHE[name] = sound

    sound = _SOUND_CACHE.get(name)
    if sound is not None:
        try:
            sound.set_volume(volume)
            sound.play()
        except pygame.error:
            pass
