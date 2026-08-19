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

_sfx_muted = False


def set_sfx_muted(muted: bool) -> None:
    global _sfx_muted
    _sfx_muted = muted


def is_sfx_muted() -> bool:
    return _sfx_muted

# Default volume by SFX name (soft ambient background work sounds and crisp combat/event cues)
_DEFAULT_VOLUMES = {
    "chop": 0.15,
    "gather": 0.12,
    "mine": 0.15,
    "build": 0.15,
    "lightning": 0.35,
    "fire": 0.30,
    "freeze": 0.30,
    "night_howl": 0.40,
    "dawn": 0.35,
}

# Cooldown between same-sound triggers to prevent multi-unit clutter (seconds)
_SFX_COOLDOWN = {
    "chop": 0.35,
    "gather": 0.35,
    "mine": 0.35,
    "build": 0.35,
    "lightning": 0.1,
    "fire": 0.1,
    "freeze": 0.1,
    "night_howl": 1.0,
    "dawn": 1.0,
}



def play_sfx(name: str, volume: float | None = None, min_interval: float | None = None) -> None:
    """Safely play a sound effect by name with anti-clutter throttling.
    Silently no-ops if muted, pygame mixer is uninitialized, or the file
    is missing."""
    if _sfx_muted or not pygame.mixer.get_init():
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


_CURRENT_BGM_TRACK: str | None = None

def play_bgm(phase: str, volume: float = 0.20) -> None:
    """Safely play background music looping for daytime or nighttime.
    Uses pygame.mixer.music so it streams smoothly without eating memory."""
    global _CURRENT_BGM_TRACK
    if not pygame.mixer.get_init():
        return

    track_name = f"{phase}_bgm"
    if _CURRENT_BGM_TRACK == track_name:
        return

    for ext in (".wav", ".ogg", ".mp3", ".m4a"):
        bgm_path = _SFX_DIR / f"{track_name}{ext}"
        if bgm_path.exists():
            try:
                pygame.mixer.music.load(str(bgm_path))
                pygame.mixer.music.set_volume(volume)
                pygame.mixer.music.play(-1, fade_ms=1000)
                _CURRENT_BGM_TRACK = track_name
                break
            except (pygame.error, OSError):
                continue


def stop_bgm(fade_ms: int = 500) -> None:
    """Fade out and stop background music."""
    global _CURRENT_BGM_TRACK
    if not pygame.mixer.get_init():
        return
    try:
        pygame.mixer.music.fadeout(fade_ms)
        _CURRENT_BGM_TRACK = None
    except pygame.error:
        pass


