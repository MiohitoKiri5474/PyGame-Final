import sys

if sys.platform == "win32":
    # Without this, Windows applies DPI-virtualization bitmap-stretching to
    # a non-DPI-aware app: the actual OS window ends up bigger than the
    # 1024x768 pygame.display.set_mode() surface, with the extra space
    # showing raw unfilled background and every screen-space calculation
    # (mouse position, HUD layout) misaligned relative to what's on screen.
    # Must run before pygame creates the window, so before importing Game.
    import ctypes

    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except (AttributeError, OSError):
        pass

from game import Game

if __name__ == "__main__":
    Game().run()
