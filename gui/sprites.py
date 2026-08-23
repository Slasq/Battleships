from pathlib import Path

import pygame

ASSETS = Path(__file__).resolve().parent.parent / "assets"

_sprites = {}
_scaled = {}
_frames = {}


def sprite(name):
    surf = _sprites.get(name)
    if surf is None:
        surf = pygame.image.load(str(ASSETS / name)).convert_alpha()
        _sprites[name] = surf
    return surf


def scaled(name, factor):
    key = (name, factor)
    surf = _scaled.get(key)
    if surf is None:
        src = sprite(name)
        surf = pygame.transform.scale(src, (src.get_width() * factor, src.get_height() * factor))
        _scaled[key] = surf
    return surf


def frame(name, size, edge=6):
    key = (name, size, edge)
    surf = _frames.get(key)
    if surf is not None:
        return surf

    src = sprite(name)
    sw, sh = src.get_size()
    w, h = size
    mid_sw, mid_sh = sw - edge * 2, sh - edge * 2
    mid_w, mid_h = w - edge * 2, h - edge * 2
    surf = pygame.Surface(size, pygame.SRCALPHA)

    def part(sx, sy, spw, sph, dx, dy, dw, dh):
        if dw <= 0 or dh <= 0:
            return
        piece = src.subsurface(pygame.Rect(sx, sy, spw, sph))
        if (dw, dh) != (spw, sph):
            piece = pygame.transform.scale(piece, (dw, dh))
        surf.blit(piece, (dx, dy))

    part(edge, edge, mid_sw, mid_sh, edge, edge, mid_w, mid_h)
    part(edge, 0, mid_sw, edge, edge, 0, mid_w, edge)
    part(edge, sh - edge, mid_sw, edge, edge, h - edge, mid_w, edge)
    part(0, edge, edge, mid_sh, 0, edge, edge, mid_h)
    part(sw - edge, edge, edge, mid_sh, w - edge, edge, edge, mid_h)
    part(0, 0, edge, edge, 0, 0, edge, edge)
    part(sw - edge, 0, edge, edge, w - edge, 0, edge, edge)
    part(0, sh - edge, edge, edge, 0, h - edge, edge, edge)
    part(sw - edge, sh - edge, edge, edge, w - edge, h - edge, edge, edge)

    _frames[key] = surf
    return surf


def tile(surf, name, factor, rect, offset_x=0, offset_y=0):
    img = scaled(name, factor)
    tw, th = img.get_size()
    start_x = rect.x - tw + (offset_x % tw)
    start_y = rect.y - th + (offset_y % th)
    clip = surf.get_clip()
    surf.set_clip(rect)
    y = start_y
    while y < rect.bottom:
        x = start_x
        while x < rect.right:
            surf.blit(img, (x, y))
            x += tw
        y += th
    surf.set_clip(clip)
