"""Audio & Sound Effects Manager.

Loads sound effects from assets/sfx/ with lazy-caching and safe headless fallback
so tests and systems without audio devices continue working cleanly.
"""

import os
import time
from pathlib import Path
from typing import TYPE_CHECKING

import pygame

_SOUND_CACHE: dict[str, pygame.mixer.Sound | None] = {}
_LAST_PLAYED: dict[str, float] = {}
_SFX_DIR = Path(__file__).parent.parent / "assets" / "sfx"

# Default volume by SFX name (soft background work sounds)
_DEFAULT_VOLUMES = {
    "chop": 0.35,
    "gather": 0.30,
}

# Cooldown between same-sound triggers to prevent multi-unit clutter (seconds)
_SFX_COOLDOWN = {
    "chop": 0.35,
    "gather": 0.35,
}


def play_sfx(name: str, volume: float | None = None, min_interval: float | None = None) -> None:
    """Safely play a sound effect by name with anti-clutter throttling.
    Silently no-ops if pygame mixer is uninitialized or file is missing."""
    if not pygame.mixer.get_init():
        return

    now = time.monotonic()
    cooldown = min_interval if min_interval is not None else _SFX_COOLDOWN.get(name, 0.0)
    if cooldown > 0.0 and now - _LAST_PLAYED.get(name, 0.0) < cooldown:
        return
    _LAST_PLAYED[name] = now

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
            vol = volume if volume is not None else _DEFAULT_VOLUMES.get(name, 0.5)
            sound.set_volume(vol)
            sound.play()
        except pygame.error:
            pass

