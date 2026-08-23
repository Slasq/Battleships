import os

import pygame

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
    dw, dh = desktop_size()
    by_w = dw * MARGIN_W / UNIT_W
    by_h = dh * MARGIN_H / UNIT_H
    return max(MIN_SCALE, min(by_w, by_h, MAX_SCALE))


class Layout:
    def __init__(self):
        self.scale = fit_scale()
        sw = round(SCREEN_W * self.scale)
        sh = round(SCREEN_H * self.scale)
        pad = round(BEZEL_PAD_UNIT * self.scale)
        gap = round(SCREEN_GAP_UNIT * self.scale)
        self.win_w = sw + pad * 2
        self.win_h = sh * 2 + gap + pad * 2
        self.top_rect = pygame.Rect(pad, pad, sw, sh)
        self.bot_rect = pygame.Rect(pad, pad + sh + gap, sw, sh)
        self.top_bezel = self.top_rect.inflate(pad, pad)
        self.bot_bezel = self.bot_rect.inflate(pad, pad)

    def local(self, pos, rect):
        x = (pos[0] - rect.x) * SCREEN_W / rect.w
        y = (pos[1] - rect.y) * SCREEN_H / rect.h
        return x, y
