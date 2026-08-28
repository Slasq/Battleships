import os

import pygame

from .settings import SETTINGS
from .theme import (
    BEZEL_PAD_UNIT,
    MARGIN_H,
    MARGIN_W,
    MAX_SCALE,
    MIN_SCALE,
    SCREEN_GAP_UNIT,
    SCREEN_H,
    SCREEN_W,
    UNIT_H,
    UNIT_W,
)


def desktop_size():
    try:
        return pygame.display.get_desktop_sizes()[0]
    except Exception:
        info = pygame.display.Info()
        return info.current_w, info.current_h


def fit_scale():
    override = os.environ.get("BATTLESHIP_SCALE")
    if override:
        try:
            value = float(override)
            if value > 0:
                return value
        except ValueError:
            pass
    choice = SETTINGS.value("scale")
    if choice:
        return float(choice)
    dw, dh = desktop_size()
    by_w = dw * MARGIN_W / UNIT_W
    by_h = dh * MARGIN_H / UNIT_H
    return max(MIN_SCALE, min(by_w, by_h, MAX_SCALE))


def screen_metrics(scale):
    return (
        round(SCREEN_W * scale),
        round(SCREEN_H * scale),
        round(BEZEL_PAD_UNIT * scale),
        round(SCREEN_GAP_UNIT * scale),
    )


def window_size(scale):
    sw, sh, pad, gap = screen_metrics(scale)
    return sw + pad * 2, sh * 2 + gap + pad * 2


class Layout:
    def __init__(self):
        self.scale = fit_scale()
        sw, sh, pad, gap = screen_metrics(self.scale)
        self.win_w, self.win_h = window_size(self.scale)
        self.top_rect = pygame.Rect(pad, pad, sw, sh)
        self.bot_rect = pygame.Rect(pad, pad + sh + gap, sw, sh)
        self.top_bezel = self.top_rect.inflate(pad, pad)
        self.bot_bezel = self.bot_rect.inflate(pad, pad)

    def local(self, pos, rect):
        x = (pos[0] - rect.x) * SCREEN_W / rect.w
        y = (pos[1] - rect.y) * SCREEN_H / rect.h
        return x, y
