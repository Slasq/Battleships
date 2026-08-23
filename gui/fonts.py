from pathlib import Path

import pygame

FONT_PATH = Path(__file__).resolve().parent.parent / "assets" / "PressStart2P-Regular.ttf"

SM = 8
MD = 8
LG = 16

_cache = {}


def font(size):
    cached = _cache.get(size)
    if cached is None:
        if FONT_PATH.exists():
            cached = pygame.font.Font(str(FONT_PATH), size)
        else:
            cached = pygame.font.SysFont("Consolas", size, bold=True)
        _cache[size] = cached
    return cached
