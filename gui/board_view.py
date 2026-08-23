import pygame

from . import overlay
from .draw import darken, diamond, draw_iso_cell, draw_text, iso_center, lerp, point_in_diamond
from .fonts import MD, SM, font
from .heatmap import heat_color
from .match import remaining_hp
from .theme import (
    AI_ORIGIN,
    CELL_CURSOR,
    CELL_HIT,
    CELL_HIT_SIDE,
    CELL_MISS,
    CELL_MISS_SIDE,
    CELL_PREDICT,
    CELL_SHIP,
    CELL_SHIP_SIDE,
    CELL_WATER,
    CELL_WATER_LIGHT,
    HP_GREEN,
    HP_RED,
    HP_YELLOW,
    HUD_BG,
    INK,
    PLAYER_ORIGIN,
    RING_HIT,
    RING_MISS,
    SCREEN_H,
    SCREEN_W,
    SKY_BOTTOM,
    SKY_TOP,
    UI_BORDER,
    WATER,
    WATER_DEEP,
)

DRAW_ORDER = sorted(range(100), key=lambda i: (i // 10 + i % 10, i // 10))

_sea = None
_shine = None


def _sea_surface():
    global _sea
    if _sea is None:
        _sea = pygame.Surface((SCREEN_W, SCREEN_H))
        horizon = int(SCREEN_H * 0.45)
        for y in range(SCREEN_H):
            if y < horizon:
                color = lerp(SKY_TOP, SKY_BOTTOM, y / horizon)
            else:
                color = lerp(WATER, WATER_DEEP, (y - horizon) / (SCREEN_H - horizon))
            pygame.draw.line(_sea, color, (0, y), (SCREEN_W, y))
    return _sea


def _shine_surface():
    global _shine
    if _shine is None:
        _shine = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        pygame.draw.polygon(_shine, (255, 255, 255, 18), [(0, 0), (280, 0), (200, 90), (0, 70)])
    return _shine


def hp_color(ratio):
    if ratio > 0.5:
        return HP_GREEN
    if ratio > 0.2:
        return HP_YELLOW
    return HP_RED


def hit_test(match, local, origin):
    lx, ly = local
    for i in range(100):
        kind = match.cell_enemy(i)
        lift = match.cell_lift(i, kind, True)
        cx, cy = iso_center(i % 10, i // 10, origin)
        if point_in_diamond(lx, ly, cx, cy - lift):
            return i
    return None


def _platform(surf, origin):
    cx, cy = origin[0], origin[1] + 36
    ellipse = pygame.Rect(0, 0, 168, 52)
    ellipse.center = (int(cx), int(cy))
    shadow = pygame.Surface(ellipse.size, pygame.SRCALPHA)
    pygame.draw.ellipse(shadow, (0, 0, 0, 70), shadow.get_rect())
    surf.blit(shadow, ellipse.topleft)


def _board(surf, match, origin, enemy):
    for i in DRAW_ORDER:
        col, row = i % 10, i // 10
        cx, cy = iso_center(col, row, origin)
        kind = match.cell_enemy(i) if enemy else match.cell_own(i)
        checker = (row + col) % 2 == 0
        bump_cell = enemy and match.shot_bump(i)
        extra_lift = 2 if bump_cell else 0
        lift_now = match.cell_lift(i, kind, enemy)
        if kind == "water":
            if enemy and match.show_heat:
                fill = heat_color(match.heat_values()[i])
                draw_iso_cell(surf, cx, cy, fill, darken(fill), lift=lift_now + extra_lift)
            else:
                fill = CELL_WATER if checker else lerp(CELL_WATER, CELL_WATER_LIGHT, 0.25)
                draw_iso_cell(surf, cx, cy, fill, darken(CELL_WATER), lift=extra_lift)
        elif kind == "ship":
            draw_iso_cell(surf, cx, cy, CELL_SHIP, CELL_SHIP_SIDE, lift=2 + extra_lift)
        elif kind == "hit":
            draw_iso_cell(surf, cx, cy, CELL_HIT, CELL_HIT_SIDE, lift=4 + extra_lift, mark="X")
        elif kind == "miss":
            draw_iso_cell(surf, cx, cy, CELL_MISS, CELL_MISS_SIDE, lift=1 + extra_lift, mark="o")

        if bump_cell:
            ring_lift = lift_now + extra_lift
            if kind == "hit":
                ring_col = RING_HIT
            elif kind == "miss":
                ring_col = RING_MISS
            else:
                ring_col = CELL_CURSOR
            pygame.draw.polygon(surf, ring_col, diamond(cx, cy - ring_lift), 3)

        if not enemy or bump_cell:
            continue
        if i == match.predicted:
            pygame.draw.polygon(surf, CELL_PREDICT, diamond(cx, cy - lift_now), 2)
        if i == match.cursor:
            pygame.draw.polygon(surf, CELL_CURSOR, diamond(cx, cy - lift_now), 2)


def _hud(surf, x, y, name, lvl, ratio):
    box = pygame.Rect(x, y, 150, 42)
    pygame.draw.rect(surf, HUD_BG, box, border_radius=10)
    pygame.draw.rect(surf, UI_BORDER, box, 3, border_radius=10)
    draw_text(surf, name, font(MD), INK, (x + 8, y + 6))
    bar = pygame.Rect(x + 30, y + 26, 78, 8)
    pygame.draw.rect(surf, (72, 64, 64), bar.inflate(4, 4), border_radius=4)
    pygame.draw.rect(surf, (224, 224, 224), bar, border_radius=3)
    inner = bar.inflate(-4, -4)
    pygame.draw.rect(surf, (80, 104, 80), inner)
    fill_w = max(0, int(inner.w * max(0.0, min(1.0, ratio))))
    if fill_w:
        pygame.draw.rect(surf, hp_color(ratio), pygame.Rect(inner.x, inner.y, fill_w, inner.h))
    draw_text(surf, "HP", font(SM), (248, 176, 48), (x + 8, y + 24), outline=(80, 48, 0))
    lvl_s = font(SM).render(f"Lv{lvl}", False, (51, 51, 51))
    surf.blit(lvl_s, (x + 142 - lvl_s.get_width(), y + 24))


def render(surf, match):
    surf.blit(_sea_surface(), (0, 0))

    _platform(surf, AI_ORIGIN)
    _platform(surf, PLAYER_ORIGIN)
    _board(surf, match, AI_ORIGIN, enemy=True)
    _board(surf, match, PLAYER_ORIGIN, enemy=False)

    ai_left, ai_total = remaining_hp(match.game.player2.indexes, match.game.player1.search)
    pl_left, pl_total = remaining_hp(match.game.player1.indexes, match.game.player2.search)
    _hud(surf, 8, 8, "AI", 99, ai_left / ai_total)
    _hud(surf, SCREEN_W - 158, SCREEN_H - 50, "GRACZ", 12, pl_left / pl_total)

    surf.blit(_shine_surface(), (0, 0))

    if match.over:
        overlay.game_over(surf, match.winner())
