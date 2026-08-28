import math

import pygame

from .draw import lerp, wrap_text
from .fonts import SM, font
from .model_select import BUTTONS, DARK_TEXT, MAX_RANK, MODELS
from .settings import anim_ticks
from .sprites import frame, sprite
from .theme import (
    HUD_BG,
    INK,
    MENU_BTN_RED_SHADOW,
    PAPER,
    SCREEN_H,
    SCREEN_W,
    SELECT_BG,
    SELECT_BG_PATTERN,
    SELECT_DESC,
    SELECT_GRID,
    SELECT_ITEM_BG,
    SELECT_ITEM_SEL,
    SELECT_ITEM_TEXT,
    SELECT_LIST_BG,
    SELECT_LIST_EDGE,
    SELECT_PLATFORM,
    SELECT_PLATFORM_EDGE,
    SELECT_SHADOW,
    SELECT_SKY_BOTTOM,
    SELECT_SKY_TOP,
    SELECT_STAT_RULE,
    SELECT_STAT_VALUE,
    UI_BORDER,
)

PAD = 10
AVATAR_RECT = pygame.Rect(PAD, PAD, 130, SCREEN_H - PAD * 2)
SPRITE_CY = 106
PLATFORM_RECT = pygame.Rect(0, 0, 100, 30)
PLATFORM_CENTER = (AVATAR_RECT.centerx, 166)
SHADOW_RECT = pygame.Rect(0, 0, 60, 10)
SHADOW_CENTER = (AVATAR_RECT.centerx, 156)

INFO_X = AVATAR_RECT.right + PAD
INFO_W = SCREEN_W - INFO_X - PAD
HEADER_RECT = pygame.Rect(INFO_X, PAD, INFO_W, 24)
STATS_RECT = pygame.Rect(
    INFO_X, HEADER_RECT.bottom + 6, INFO_W, SCREEN_H - HEADER_RECT.bottom - 6 - PAD
)

STAT_ROWS = [("EPOKI:", "epochs"), ("WINRATE:", "winrate"), ("EPSILON:", "eps")]
STAT_TOP = STATS_RECT.y + 10
STAT_LINE = 16
DESC_TOP = STAT_TOP + STAT_LINE * len(STAT_ROWS) + 8
DESC_LINE = 11

WIN_LABEL_Y = STATS_RECT.y + 112
WIN_BAR = pygame.Rect(STATS_RECT.x + 8, STATS_RECT.y + 126, STATS_RECT.w - 16, 14)
WIN_TICKS = 4

RANK_LABEL_Y = STATS_RECT.bottom - 30
RANK_PIP = 12
RANK_GAP = 4
RANK_Y = STATS_RECT.bottom - 18

AURA_RINGS = 3
AURA_STEP = 9

STEP_RECT = pygame.Rect(PAD, PAD, SCREEN_W - PAD * 2, 20)
LIST_RECT = pygame.Rect(PAD, STEP_RECT.bottom + 6, SCREEN_W - PAD * 2, 142)
ITEM_GAP = 3
ITEM_H = (LIST_RECT.h - 8 - ITEM_GAP * (len(MODELS) - 1)) // len(MODELS)
ITEM_RECTS = [
    pygame.Rect(
        LIST_RECT.x + 4,
        LIST_RECT.y + 4 + i * (ITEM_H + ITEM_GAP),
        LIST_RECT.w - 8,
        ITEM_H,
    )
    for i in range(len(MODELS))
]

BTN_GAP = 10
BTN_W = (SCREEN_W - PAD * 2 - BTN_GAP) // 2
BTN_TOP = LIST_RECT.bottom + PAD
BTN_H = SCREEN_H - BTN_TOP - PAD
BUTTON_RECTS = [
    pygame.Rect(PAD + i * (BTN_W + BTN_GAP), BTN_TOP, BTN_W, BTN_H)
    for i in range(len(BUTTONS))
]

SHAKE_STEPS = ((1, -1), (-1, -2), (-2, 1))

_sky = None
_pattern = None


def _sky_surface():
    global _sky
    if _sky is None:
        _sky = pygame.Surface((SCREEN_W, SCREEN_H))
        for y in range(SCREEN_H):
            pygame.draw.line(
                _sky,
                lerp(SELECT_SKY_TOP, SELECT_SKY_BOTTOM, y / (SCREEN_H - 1)),
                (0, y),
                (SCREEN_W, y),
            )
        grid = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        for x in range(0, SCREEN_W, 16):
            pygame.draw.line(grid, (*SELECT_GRID, 102), (x, 0), (x, SCREEN_H))
        for y in range(0, SCREEN_H, 16):
            pygame.draw.line(grid, (*SELECT_GRID, 102), (0, y), (SCREEN_W, y))
        _sky.blit(grid, (0, 0))
    return _sky


def _pattern_surface():
    global _pattern
    if _pattern is None:
        _pattern = pygame.Surface((SCREEN_W, SCREEN_H))
        _pattern.fill(SELECT_BG)
        for y in range(0, SCREEN_H, 16):
            for x in range(0, SCREEN_W, 16):
                pygame.draw.rect(_pattern, SELECT_BG_PATTERN, pygame.Rect(x, y, 8, 8))
                pygame.draw.rect(_pattern, SELECT_BG_PATTERN, pygame.Rect(x + 8, y + 8, 8, 8))
    return _pattern


def _wave(ticks, period):
    return math.sin(ticks / period * math.tau)


def _anim_state(model, ticks):
    anim = model["anim"]
    if anim in ("float", "kraken"):
        period = 3000 if anim == "kraken" else 4000
        return 0, round(-4 - 4 * _wave(ticks, period)), 1.0
    if anim == "shake":
        return (*SHAKE_STEPS[(ticks // 120) % len(SHAKE_STEPS)], 1.0)
    if anim == "pulse":
        return 0, 0, 1.0 + 0.05 * (0.5 + 0.5 * _wave(ticks, 2000))
    return 0, 0, 1.0


def _ellipse(surf, size, center, color, alpha, edge=None):
    box = pygame.Rect(0, 0, *size)
    box.center = center
    layer = pygame.Surface(box.size, pygame.SRCALPHA)
    pygame.draw.ellipse(layer, (*color, alpha), layer.get_rect())
    if edge is not None:
        pygame.draw.ellipse(layer, (*edge, min(255, alpha + 60)), layer.get_rect(), 2)
    surf.blit(layer, box.topleft)


def _aura(surf, model, ticks):
    pulse = 0.5 + 0.5 * _wave(ticks, 2400)
    base = 26 + model["rank"] * 7
    for i in range(AURA_RINGS):
        radius = base + i * AURA_STEP + round(pulse * 3)
        alpha = max(0, 54 - i * 16 - round(pulse * 12))
        if alpha <= 0:
            continue
        layer = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(
            layer, (*model["color"], alpha), (radius, radius), radius, 2 + (i == 0)
        )
        surf.blit(layer, layer.get_rect(center=(AVATAR_RECT.centerx, SPRITE_CY)))


def _avatar(surf, model, ticks):
    _aura(surf, model, ticks)
    _ellipse(
        surf,
        PLATFORM_RECT.size,
        PLATFORM_CENTER,
        SELECT_PLATFORM,
        70,
        SELECT_PLATFORM_EDGE,
    )
    _ellipse(surf, (PLATFORM_RECT.w - 18, PLATFORM_RECT.h - 8), PLATFORM_CENTER, model["color"], 70)

    dx, dy, scale = _anim_state(model, ticks)
    lift = max(0, -dy)
    shadow_w = SHADOW_RECT.w - lift * 2
    if shadow_w > 8:
        _ellipse(
            surf,
            (shadow_w, SHADOW_RECT.h),
            SHADOW_CENTER,
            SELECT_SHADOW,
            max(40, 140 - lift * 10),
        )

    img = sprite(model["sprite"])
    img = pygame.transform.scale(
        img,
        (
            round(img.get_width() * model["scale"] * scale),
            round(img.get_height() * model["scale"] * scale),
        ),
    )
    surf.blit(img, img.get_rect(center=(AVATAR_RECT.centerx + dx, SPRITE_CY + dy)))


def _panel(surf, rect, fill):
    pygame.draw.rect(surf, fill, rect, border_radius=8)
    pygame.draw.rect(surf, UI_BORDER, rect, 3, border_radius=8)


def _info(surf, state):
    model = state.current()
    accent = state.accent()
    on_accent = state.on_accent()

    _panel(surf, HEADER_RECT, accent)
    glyph = font(SM).render(model["name"], False, on_accent)
    pos = (
        HEADER_RECT.centerx - glyph.get_width() // 2,
        HEADER_RECT.centery - glyph.get_height() // 2,
    )
    if on_accent == PAPER:
        surf.blit(font(SM).render(model["name"], False, INK), (pos[0] + 1, pos[1] + 1))
    surf.blit(glyph, pos)

    _panel(surf, STATS_RECT, HUD_BG)

    value_color = SELECT_STAT_VALUE if accent in DARK_TEXT else accent
    x0 = STATS_RECT.x + 8
    x1 = STATS_RECT.right - 8
    y = STAT_TOP
    for label, key in STAT_ROWS:
        surf.blit(font(SM).render(label, False, INK), (x0, y))
        value = font(SM).render(model[key], False, value_color)
        surf.blit(value, (x1 - value.get_width(), y))
        for x in range(x0, x1, 4):
            pygame.draw.line(surf, SELECT_STAT_RULE, (x, y + 11), (x + 1, y + 11))
        y += STAT_LINE

    y = DESC_TOP
    for line in wrap_text(model["desc"], font(SM), STATS_RECT.w - 16):
        surf.blit(font(SM).render(line, False, SELECT_DESC), (x0, y))
        y += DESC_LINE

    surf.blit(font(SM).render("SKUTECZNOSC", False, SELECT_DESC), (x0, WIN_LABEL_Y))
    pygame.draw.rect(surf, SELECT_BG, WIN_BAR)
    ratio = float(model["winrate"].rstrip("%")) / 100
    fill = WIN_BAR.copy()
    fill.w = max(2, round(WIN_BAR.w * ratio))
    pygame.draw.rect(surf, accent, fill)
    pygame.draw.rect(surf, PAPER, pygame.Rect(fill.x + 2, fill.y + 2, fill.w - 4, 2))
    for i in range(1, WIN_TICKS):
        x = WIN_BAR.x + round(WIN_BAR.w * i / WIN_TICKS)
        pygame.draw.line(surf, INK, (x, WIN_BAR.y), (x, WIN_BAR.bottom - 1))
    pygame.draw.rect(surf, INK, WIN_BAR, 2)

    surf.blit(font(SM).render("POZIOM", False, INK), (x0, RANK_LABEL_Y))
    for i in range(MAX_RANK):
        pip = pygame.Rect(x0 + i * (RANK_PIP + RANK_GAP), RANK_Y, RANK_PIP, RANK_PIP)
        pygame.draw.rect(surf, accent if i < model["rank"] else HUD_BG, pip, border_radius=3)
        pygame.draw.rect(surf, INK, pip, 2, border_radius=3)
        if i < model["rank"]:
            pygame.draw.rect(surf, PAPER, pygame.Rect(pip.x + 3, pip.y + 3, 3, 3))


def render_top(surf, state):
    surf.blit(_sky_surface(), (0, 0))
    _avatar(surf, state.current(), anim_ticks())
    _info(surf, state)


def _badge(surf, model, right, cy):
    color = INK if model["color"] in DARK_TEXT else PAPER
    glyph = font(SM).render(model["diff"], False, color)
    rect = pygame.Rect(0, 0, glyph.get_width() + 8, glyph.get_height() + 6)
    rect.midright = (right, cy)
    pygame.draw.rect(surf, model["color"], rect, border_radius=4)
    pygame.draw.rect(surf, INK, rect, 1, border_radius=4)
    surf.blit(glyph, (rect.x + 4, rect.y + 3))


def _item(surf, index, rect, selected):
    model = MODELS[index]
    if selected:
        pygame.draw.rect(surf, SELECT_ITEM_SEL, rect, border_radius=4)
        pygame.draw.rect(surf, INK, rect, 2, border_radius=4)
        glow = pygame.Surface((rect.w - 6, rect.h // 2), pygame.SRCALPHA)
        glow.fill((255, 255, 255, 46))
        surf.blit(glow, (rect.x + 3, rect.y + 3))
        text_color = PAPER
    else:
        pygame.draw.rect(surf, SELECT_ITEM_BG, rect, border_radius=4)
        text_color = SELECT_ITEM_TEXT

    stripe = pygame.Rect(rect.x + 4, rect.y + 5, 4, rect.h - 10)
    pygame.draw.rect(surf, model["color"], stripe, border_radius=2)
    pygame.draw.rect(surf, INK, stripe, 1, border_radius=2)

    glyph = font(SM).render(model["name"], False, text_color)
    surf.blit(glyph, (stripe.right + 6, rect.centery - glyph.get_height() // 2))
    _badge(surf, model, rect.right - 8, rect.centery)


def _button(surf, index, rect, focused, confirm_label):
    label, action = BUTTONS[index]
    red = action == "back"
    if not red:
        label = confirm_label
    surf.blit(frame("btn_frame_red.png" if red else "btn_frame_gold.png", rect.size), rect.topleft)

    if focused:
        glow = pygame.Surface((rect.w - 12, rect.h - 12), pygame.SRCALPHA)
        glow.fill((255, 255, 255, 46))
        surf.blit(glow, (rect.x + 6, rect.y + 6))

    color, shadow = (PAPER, MENU_BTN_RED_SHADOW) if red else (INK, None)
    glyph = font(SM).render(label, False, color)
    pos = (rect.centerx - glyph.get_width() // 2, rect.centery - glyph.get_height() // 2)
    if shadow is not None:
        surf.blit(font(SM).render(label, False, shadow), (pos[0] + 1, pos[1] + 1))
    surf.blit(glyph, pos)


def _step_bar(surf, state):
    pygame.draw.rect(surf, SELECT_LIST_EDGE, STEP_RECT, border_radius=6)
    pygame.draw.rect(surf, INK, STEP_RECT, 2, border_radius=6)

    label = font(SM).render(state.prompt(), False, PAPER)
    surf.blit(label, (STEP_RECT.x + 8, STEP_RECT.centery - label.get_height() // 2))

    picked = state.picked()
    if not picked:
        return
    text = f"VS {picked[0]['name']}"
    glyph = font(SM).render(text, False, PAPER)
    x = STEP_RECT.right - glyph.get_width() - 8
    y = STEP_RECT.centery - glyph.get_height() // 2
    chip = pygame.Rect(x - 14, STEP_RECT.centery - 5, 10, 10)
    pygame.draw.rect(surf, picked[0]["color"], chip, border_radius=2)
    pygame.draw.rect(surf, INK, chip, 2, border_radius=2)
    surf.blit(font(SM).render(text, False, INK), (x + 1, y + 1))
    surf.blit(glyph, (x, y))


def render_bottom(surf, state):
    surf.blit(_pattern_surface(), (0, 0))
    _step_bar(surf, state)
    pygame.draw.rect(surf, SELECT_LIST_BG, LIST_RECT, border_radius=8)
    pygame.draw.rect(surf, SELECT_LIST_EDGE, LIST_RECT, 3, border_radius=8)
    for i, rect in enumerate(ITEM_RECTS):
        _item(surf, i, rect, i == state.selected)
    for i, rect in enumerate(BUTTON_RECTS):
        _button(surf, i, rect, i == state.button, state.confirm_label())


def hit_test_items(local):
    for i, rect in enumerate(ITEM_RECTS):
        if rect.collidepoint(local):
            return i
    return None


def hit_test_buttons(local):
    for i, rect in enumerate(BUTTON_RECTS):
        if rect.collidepoint(local):
            return i
    return None
