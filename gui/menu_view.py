import pygame

from .draw import tracked_text
from .fonts import SM, font
from .menu import ITEMS, READY
from .sprites import frame, scaled, tile
from .theme import (
    BADGE_BG,
    INK,
    LOGO_SHADOW,
    LOGO_YELLOW,
    MENU_BG,
    MENU_BG_PATTERN,
    MENU_BTN_RED_SHADOW,
    MENU_BTN_TEXT,
    MENU_CLOUD,
    MENU_CLOUD_SHADE,
    MENU_CURSOR,
    MENU_SEA,
    MENU_SEA_EDGE,
    MENU_SKY_BANDS,
    MENU_WATER_LINE,
    PAPER,
    SCREEN_H,
    SCREEN_W,
)

WATER_TOP = int(SCREEN_H * MENU_WATER_LINE)
WATER_RECT = pygame.Rect(0, WATER_TOP, SCREEN_W, SCREEN_H - WATER_TOP)

WAVE_SCALE = 2
SHIP_SCALE = 3
SHIP_Y = 150
PRESS_Y = 218

LOGO_SIZE = 28
LOGO_TRACK = -2
LOGO_TOP = 18
LOGO_LINE = 34

CLOUDS = [
    (16, 104, 4, 4.0),
    (208, 92, 3, 6.5),
    (120, 128, 3, 3.0),
    (276, 124, 2, 5.0),
    (56, 22, 3, 2.5),
]
CLOUD_ROWS = [(1, 0, 4), (0, 1, 6), (0, 2, 7)]

BADGE_POS = (190, 70)

BTN_W, BTN_H, BTN_GAP = 220, 34, 10
BTN_X = (SCREEN_W - BTN_W) // 2
BTN_TOP = (SCREEN_H - (BTN_H * len(ITEMS) + BTN_GAP * (len(ITEMS) - 1))) // 2

BUTTON_RECTS = [
    pygame.Rect(BTN_X, BTN_TOP + i * (BTN_H + BTN_GAP), BTN_W, BTN_H)
    for i in range(len(ITEMS))
]

_sky = None
_pattern = None
_logo = None
_badge_img = None
_shine = None


def _sky_surface():
    global _sky
    if _sky is None:
        _sky = pygame.Surface((SCREEN_W, SCREEN_H))
        for start, end, color in MENU_SKY_BANDS:
            band = pygame.Rect(0, int(SCREEN_H * start), SCREEN_W, 0)
            band.height = int(SCREEN_H * end) - band.y
            pygame.draw.rect(_sky, color, band)
        pygame.draw.rect(_sky, MENU_SEA, WATER_RECT)
    return _sky


def _pattern_surface():
    global _pattern
    if _pattern is None:
        tile_surf = pygame.Surface((16, 16))
        tile_surf.fill(MENU_BG)
        for oy, ox in ((0, 0), (8, 8)):
            for y in range(16):
                for x in range(16):
                    p = ((x + 0.5) + (15.5 - y)) / 32
                    if p < 0.25 or p >= 0.75:
                        tile_surf.set_at(((x + ox) % 16, (y + oy) % 16), MENU_BG_PATTERN)
        _pattern = pygame.Surface((SCREEN_W, SCREEN_H))
        for y in range(0, SCREEN_H, 16):
            for x in range(0, SCREEN_W, 16):
                _pattern.blit(tile_surf, (x, y))
    return _pattern


def _shine_surface():
    global _shine
    if _shine is None:
        _shine = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        pygame.draw.polygon(_shine, (255, 255, 255, 18), [(0, 0), (280, 0), (200, 90), (0, 70)])
    return _shine


def _badge(text):
    glyph = font(SM).render(text, False, PAPER)
    w, h = glyph.get_width() + 12, glyph.get_height() + 10
    surf = pygame.Surface((w + 2, h + 2), pygame.SRCALPHA)
    body = pygame.Rect(0, 0, w, h)
    pygame.draw.rect(surf, INK, body.move(2, 2), border_radius=6)
    pygame.draw.rect(surf, BADGE_BG, body, border_radius=6)
    pygame.draw.rect(surf, INK, body, 2, border_radius=6)
    surf.blit(glyph, (6, 5))
    return pygame.transform.rotate(surf, 10)


def _logo_surface():
    global _logo
    if _logo is not None:
        return _logo

    glyph_font = font(LOGO_SIZE)
    lines = ["BATTLE", "SHIP"]
    fills = [tracked_text(t, glyph_font, LOGO_YELLOW, LOGO_TRACK) for t in lines]
    inks = [tracked_text(t, glyph_font, INK, LOGO_TRACK) for t in lines]
    blues = [tracked_text(t, glyph_font, LOGO_SHADOW, LOGO_TRACK) for t in lines]

    width = max(g.get_width() for g in fills) + 10
    height = LOGO_LINE * (len(lines) - 1) + fills[-1].get_height() + 10
    surf = pygame.Surface((width, height), pygame.SRCALPHA)

    for i, fill in enumerate(fills):
        x = (width - fill.get_width()) // 2
        y = i * LOGO_LINE
        for dx, dy in ((4, 4), (3, 4), (4, 3)):
            surf.blit(inks[i], (x + dx, y + dy))
        surf.blit(blues[i], (x + 3, y + 3))
        for dx in (-2, -1, 0, 1, 2):
            for dy in (-2, -1, 0, 1, 2):
                if dx or dy:
                    surf.blit(inks[i], (x + dx, y + dy))
        surf.blit(fill, (x, y))

    _logo = surf
    return _logo


def _badge_surface():
    global _badge_img
    if _badge_img is None:
        _badge_img = _badge("DQN VER.")
    return _badge_img


def _cloud(surf, x, y, unit):
    for ox, oy, w in CLOUD_ROWS:
        color = MENU_CLOUD_SHADE if oy == 2 else MENU_CLOUD
        pygame.draw.rect(surf, color, pygame.Rect(x + ox * unit, y + oy * unit, w * unit, unit))


def _clouds(surf, ticks):
    span = SCREEN_W + 80
    for base_x, y, unit, speed in CLOUDS:
        x = (base_x + ticks * speed / 1000.0) % span - 40
        _cloud(surf, int(x), y, unit)


def _water(surf, ticks):
    tile(surf, "wave_back.png", WAVE_SCALE, WATER_RECT, offset_x=int(ticks * 32 / 12000.0))
    tile(surf, "wave_front.png", WAVE_SCALE, WATER_RECT, offset_x=int(ticks * 64 / 8000.0))
    pygame.draw.line(surf, MENU_SEA_EDGE, (0, WATER_TOP), (SCREEN_W, WATER_TOP), 2)
    shade_h = int(WATER_RECT.h * 0.3)
    shade = pygame.Surface((SCREEN_W, shade_h), pygame.SRCALPHA)
    for y in range(shade_h):
        alpha = int(102 * (1 - y / shade_h))
        pygame.draw.line(shade, (*MENU_SEA_EDGE, alpha), (0, y), (SCREEN_W, y))
    surf.blit(shade, (0, WATER_TOP))


def _ship(surf, ticks):
    img = scaled("menu_ship.png", SHIP_SCALE)
    bob = -2 if (ticks // 2000) % 2 else 0
    x = (SCREEN_W - img.get_width()) // 2
    y = SHIP_Y + bob

    mirror = pygame.transform.flip(img, False, True)
    mirror.set_alpha(46)
    clip = surf.get_clip()
    surf.set_clip(pygame.Rect(x, y + img.get_height() - 6, img.get_width(), 14))
    surf.blit(mirror, (x, y + img.get_height() - 4))
    surf.set_clip(clip)

    surf.blit(img, (x, y))


def render_top(surf):
    ticks = pygame.time.get_ticks()
    surf.blit(_sky_surface(), (0, 0))
    _clouds(surf, ticks)
    _water(surf, ticks)
    _ship(surf, ticks)

    logo = _logo_surface()
    surf.blit(logo, ((SCREEN_W - logo.get_width()) // 2, LOGO_TOP))
    surf.blit(_badge_surface(), BADGE_POS)

    if (ticks // 500) % 2 == 0:
        glyph = font(SM).render("NACISNIJ START", False, PAPER)
        pos = ((SCREEN_W - glyph.get_width()) // 2, PRESS_Y)
        shadow = font(SM).render("NACISNIJ START", False, INK)
        for dx, dy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
            surf.blit(shadow, (pos[0] + dx, pos[1] + dy))
        surf.blit(glyph, pos)

    surf.blit(_shine_surface(), (0, 0))


def _button(surf, index, rect, selected):
    label, action = ITEMS[index]
    red = action == "quit"
    surf.blit(frame("btn_frame_red.png" if red else "btn_frame.png", rect.size), rect.topleft)

    if selected:
        glow = pygame.Surface((rect.w - 12, rect.h - 12), pygame.SRCALPHA)
        glow.fill((255, 255, 255, 46))
        surf.blit(glow, (rect.x + 6, rect.y + 6))

    color = PAPER if red else MENU_BTN_TEXT
    if action not in READY and not selected:
        color = (128, 144, 160) if not red else PAPER
    glyph = font(SM).render(label, False, color)
    pos = (rect.centerx - glyph.get_width() // 2, rect.centery - glyph.get_height() // 2)
    if red:
        shadow = font(SM).render(label, False, MENU_BTN_RED_SHADOW)
        surf.blit(shadow, (pos[0] + 1, pos[1] + 1))
    surf.blit(glyph, pos)

    if selected:
        cx, cy = rect.x + 14, rect.centery
        pygame.draw.circle(surf, INK, (cx, cy), 6)
        pygame.draw.circle(surf, PAPER if red else MENU_CURSOR, (cx, cy), 4)


def render_bottom(surf, menu):
    surf.blit(_pattern_surface(), (0, 0))
    for i, rect in enumerate(BUTTON_RECTS):
        _button(surf, i, rect, i == menu.selected)


def hit_test(local):
    for i, rect in enumerate(BUTTON_RECTS):
        if rect.collidepoint(local):
            return i
    return None
