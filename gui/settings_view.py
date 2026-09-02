import math

import pygame

from .draw import draw_iso_cell, iso_center, lerp, wrap_text
from .fonts import SM, font
from .heatmap import heat_color, normalized_density
from .settings import BUTTONS, OPTIONS
from .sprites import frame, scaled, tile
from .theme import (
    CELL_HIT,
    CELL_MISS,
    CELL_SHIP,
    CELL_SHIP_SIDE,
    CELL_WATER,
    CELL_WATER_LIGHT,
    INK,
    MENU_BTN_RED_SHADOW,
    MENU_BTN_TEXT,
    MENU_CURSOR,
    MENU_SEA_EDGE,
    PAPER,
    SCREEN_H,
    SCREEN_W,
    SET_ACCENT,
    SET_ARROW,
    SET_ARROW_HOT,
    SET_CHIP_BG,
    SET_GRID,
    SET_LABEL,
    SET_PANEL,
    SET_PANEL_EDGE,
    SET_PREV_DESK,
    SET_PREV_SEA,
    SET_PREV_SKY,
    SET_PREV_TRACK,
    SET_ROW_BG,
    SET_ROW_SEL,
    SET_ROW_TEXT,
    SET_SKY_BOTTOM,
    SET_SKY_TOP,
    SET_VALUE,
)

PAD = 10

HEADER_RECT = pygame.Rect(PAD, PAD, SCREEN_W - PAD * 2, 24)
PREVIEW_RECT = pygame.Rect(PAD, HEADER_RECT.bottom + 8, SCREEN_W - PAD * 2, 118)
VALUE_RECT = pygame.Rect(PAD, PREVIEW_RECT.bottom + 6, SCREEN_W - PAD * 2, 24)
DESC_TOP = VALUE_RECT.bottom + 8
DESC_LINE = 11
HINT_Y = SCREEN_H - 14

ROW_H = 28
ROW_GAP = 4
ROW_RECTS = [
    pygame.Rect(PAD, PAD + i * (ROW_H + ROW_GAP), SCREEN_W - PAD * 2, ROW_H)
    for i in range(len(OPTIONS))
]

ARROW_W = 18
VALUE_W = 100

BTN_GAP = 10
BTN_TOP = ROW_RECTS[-1].bottom + PAD
BTN_H = SCREEN_H - BTN_TOP - PAD
BTN_W = (SCREEN_W - PAD * 2 - BTN_GAP) // 2
BUTTON_RECTS = [
    pygame.Rect(PAD + i * (BTN_W + BTN_GAP), BTN_TOP, BTN_W, BTN_H) for i in range(len(BUTTONS))
]

HEAT_CELL = 9
GRID_N = 10

_sky = None
_heat = None


def _sky_surface():
    global _sky
    if _sky is None:
        _sky = pygame.Surface((SCREEN_W, SCREEN_H))
        for y in range(SCREEN_H):
            pygame.draw.line(
                _sky,
                lerp(SET_SKY_TOP, SET_SKY_BOTTOM, y / (SCREEN_H - 1)),
                (0, y),
                (SCREEN_W, y),
            )
        for x in range(0, SCREEN_W, 16):
            pygame.draw.line(_sky, SET_GRID, (x, 0), (x, SCREEN_H))
        for y in range(0, SCREEN_H, 16):
            pygame.draw.line(_sky, SET_GRID, (0, y), (SCREEN_W, y))
    return _sky


def _demo_search():
    search = ["U"] * 100
    for idx in (3, 11, 27, 40, 58, 66, 74, 81, 95):
        search[idx] = "M"
    search[45] = "H"
    return search


def _heat_values():
    global _heat
    if _heat is None:
        _heat = normalized_density(_demo_search())
    return _heat


def _row_parts(rect):
    right = pygame.Rect(rect.right - 10 - ARROW_W, rect.centery - 9, ARROW_W, 18)
    value = pygame.Rect(right.x - 4 - VALUE_W, rect.centery - 10, VALUE_W, 20)
    left = pygame.Rect(value.x - 4 - ARROW_W, rect.centery - 9, ARROW_W, 18)
    return left, value, right


def _prev_speed(surf, box, value, ticks):
    track = pygame.Rect(box.x + 10, box.centery + 6, box.w - 20, 12)
    pygame.draw.rect(surf, SET_PREV_TRACK, track, border_radius=6)
    pygame.draw.rect(surf, SET_PANEL_EDGE, track, 2, border_radius=6)

    period = max(600, int(2200 * value))
    phase = (ticks % period) / period
    x = track.x + 8 + round((track.w - 16) * (0.5 - 0.5 * math.cos(phase * math.tau)))

    for i in range(4):
        pip = pygame.Rect(0, 0, 4, 4)
        pip.center = (x - 8 - i * 7, track.centery)
        if pip.x > track.x:
            fade = 120 - i * 30
            layer = pygame.Surface(pip.size, pygame.SRCALPHA)
            layer.fill((*SET_ACCENT, fade))
            surf.blit(layer, pip.topleft)

    ship = scaled("menu_ship.png", 1)
    surf.blit(ship, ship.get_rect(center=(x, track.y - 6)))

    steps = len(OPTIONS[0]["values"])
    level = [v for _, v in OPTIONS[0]["values"]].index(value)
    bar_w = 22
    total = steps * bar_w + (steps - 1) * 6
    bx = box.centerx - total // 2
    for i in range(steps):
        bar = pygame.Rect(bx + i * (bar_w + 6), box.y + 8, bar_w, 10 + i * 4)
        bar.bottom = box.y + 34
        pygame.draw.rect(surf, SET_ACCENT if i <= level else SET_PREV_TRACK, bar, border_radius=2)
        pygame.draw.rect(surf, SET_PANEL_EDGE, bar, 1, border_radius=2)


def _prev_heatmap(surf, box, value, ticks):
    size = HEAT_CELL * GRID_N
    grid = pygame.Rect(0, 0, size, size)
    grid.center = box.center
    search = _demo_search()
    heat = _heat_values()
    pulse = 0.85 + 0.15 * math.sin(ticks / 700.0)
    for row in range(GRID_N):
        for col in range(GRID_N):
            idx = row * GRID_N + col
            cell = pygame.Rect(
                grid.x + col * HEAT_CELL, grid.y + row * HEAT_CELL, HEAT_CELL - 1, HEAT_CELL - 1
            )
            state = search[idx]
            if state == "M":
                color = CELL_MISS
            elif state == "H":
                color = CELL_HIT
            elif value:
                color = heat_color(heat[idx] * pulse)
            else:
                color = CELL_WATER if (row + col) % 2 else CELL_WATER_LIGHT
            pygame.draw.rect(surf, color, cell)
    pygame.draw.rect(surf, SET_PANEL_EDGE, grid.inflate(4, 4), 2)


def _prev_iso(surf, box, value, ticks):
    board = 6
    if value:
        origin = (box.centerx, box.centery - board * 4 + 6)
        for row in range(board):
            for col in range(board):
                cx, cy = iso_center(col, row, origin)
                ship = (row == 2 and 1 <= col <= 3) or (col == 4 and 3 <= row <= 4)
                fill = CELL_SHIP if ship else CELL_WATER
                side = CELL_SHIP_SIDE if ship else MENU_SEA_EDGE
                draw_iso_cell(surf, cx, cy, fill, side, lift=2 if ship else 0)
        return

    cell = 14
    grid = pygame.Rect(0, 0, cell * board, cell * board)
    grid.center = box.center
    for row in range(board):
        for col in range(board):
            rect = pygame.Rect(
                grid.x + col * cell, grid.y + row * cell, cell - 1, cell - 1
            )
            ship = (row == 2 and 1 <= col <= 3) or (col == 4 and 3 <= row <= 4)
            pygame.draw.rect(surf, CELL_SHIP if ship else CELL_WATER, rect)
            pygame.draw.rect(surf, MENU_SEA_EDGE, rect, 1)
    pygame.draw.rect(surf, SET_PANEL_EDGE, grid.inflate(4, 4), 2)


def _prev_anim(surf, box, value, ticks):
    ticks = ticks if value else 0
    stage = box.inflate(-24, -20)
    pygame.draw.rect(surf, SET_PREV_SKY, stage)
    sea = pygame.Rect(stage.x, stage.centery + 4, stage.w, stage.bottom - stage.centery - 4)
    pygame.draw.rect(surf, SET_PREV_SEA, sea)

    clip = surf.get_clip()
    surf.set_clip(sea)
    tile(surf, "wave_back.png", 1, sea, offset_x=int(ticks * 32 / 4000.0))
    tile(surf, "wave_front.png", 1, sea, offset_x=int(ticks * 64 / 3000.0))
    surf.set_clip(clip)
    pygame.draw.line(surf, MENU_SEA_EDGE, (sea.x, sea.y), (sea.right, sea.y), 2)

    ship = scaled("menu_ship.png", 2)
    bob = -2 if (ticks // 500) % 2 else 0
    surf.blit(ship, ship.get_rect(midbottom=(stage.centerx, sea.y + 8 + bob)))

    pygame.draw.rect(surf, SET_PANEL_EDGE, stage, 2)
    if not value:
        glyph = font(SM).render("STOP-KLATKA", False, INK)
        pos = (stage.centerx - glyph.get_width() // 2, stage.y + 6)
        pygame.draw.rect(surf, SET_ACCENT, pygame.Rect(pos[0] - 4, pos[1] - 3, glyph.get_width() + 8, glyph.get_height() + 6))
        surf.blit(glyph, pos)


def _prev_scale(surf, box, value, ticks):
    from .window import fit_scale, window_size

    scale = value or fit_scale()
    win_w, win_h = window_size(scale)

    desk = pygame.Rect(0, 0, box.w - 40, box.h - 34)
    desk.center = (box.centerx, box.centery - 6)
    pygame.draw.rect(surf, SET_PREV_DESK, desk)
    pygame.draw.rect(surf, SET_PANEL_EDGE, desk, 2)

    ratio = min(1.0, win_h / 1080.0)
    inner_h = max(12, round(desk.h * ratio))
    inner_w = max(10, round(inner_h * win_w / win_h))
    inner = pygame.Rect(0, 0, inner_w, inner_h)
    inner.center = desk.center
    pygame.draw.rect(surf, SET_ACCENT, inner)
    pygame.draw.rect(surf, INK, inner, 2)
    pygame.draw.line(surf, INK, (inner.x, inner.centery), (inner.right, inner.centery), 2)

    text = f"{win_w} x {win_h} PX"
    glyph = font(SM).render(text, False, SET_VALUE)
    surf.blit(glyph, (box.centerx - glyph.get_width() // 2, box.bottom - 12))


PREVIEWS = {
    "speed": _prev_speed,
    "heatmap": _prev_heatmap,
    "iso": _prev_iso,
    "anim": _prev_anim,
    "scale": _prev_scale,
}


def render_top(surf, state):
    ticks = pygame.time.get_ticks()
    surf.blit(_sky_surface(), (0, 0))

    row = state.preview_row()
    option = OPTIONS[row]

    pygame.draw.rect(surf, SET_PANEL, HEADER_RECT, border_radius=6)
    pygame.draw.rect(surf, SET_ACCENT, HEADER_RECT, 2, border_radius=6)
    title = font(SM).render("USTAWIENIA", False, SET_ACCENT)
    surf.blit(title, (HEADER_RECT.x + 8, HEADER_RECT.centery - title.get_height() // 2))
    counter = font(SM).render(f"{row + 1}/{len(OPTIONS)}", False, SET_LABEL)
    surf.blit(
        counter,
        (HEADER_RECT.right - counter.get_width() - 8, HEADER_RECT.centery - counter.get_height() // 2),
    )

    pygame.draw.rect(surf, SET_PANEL, PREVIEW_RECT, border_radius=8)
    pygame.draw.rect(surf, SET_PANEL_EDGE, PREVIEW_RECT, 2, border_radius=8)
    clip = surf.get_clip()
    surf.set_clip(PREVIEW_RECT.inflate(-4, -4))
    PREVIEWS[option["key"]](surf, PREVIEW_RECT.inflate(-16, -16), state.value(option["key"]), ticks)
    surf.set_clip(clip)

    pygame.draw.rect(surf, SET_PANEL, VALUE_RECT, border_radius=6)
    pygame.draw.rect(surf, SET_PANEL_EDGE, VALUE_RECT, 2, border_radius=6)
    label = font(SM).render(option["label"], False, SET_LABEL)
    surf.blit(label, (VALUE_RECT.x + 8, VALUE_RECT.centery - label.get_height() // 2))
    value = font(SM).render(state.value_label(row), False, SET_ACCENT)
    surf.blit(
        value,
        (VALUE_RECT.right - value.get_width() - 8, VALUE_RECT.centery - value.get_height() // 2),
    )

    y = DESC_TOP
    for line in wrap_text(option["desc"], font(SM), PREVIEW_RECT.w - 4):
        surf.blit(font(SM).render(line, False, SET_VALUE), (PAD + 2, y))
        y += DESC_LINE

    hint = "LEWO/PRAWO ZMIENIA WARTOSC"
    glyph = font(SM).render(hint, False, SET_LABEL)
    surf.blit(glyph, ((SCREEN_W - glyph.get_width()) // 2, HINT_Y))


def _arrow(surf, rect, facing_left, active):
    color = SET_ARROW_HOT if active else SET_ARROW
    cx, cy = rect.center
    if facing_left:
        points = [(cx + 4, cy - 6), (cx + 4, cy + 6), (cx - 5, cy)]
    else:
        points = [(cx - 4, cy - 6), (cx - 4, cy + 6), (cx + 5, cy)]
    pygame.draw.polygon(surf, color, points)
    pygame.draw.polygon(surf, INK, points, 1)


def _row(surf, index, rect, state):
    selected = state.selected == index
    option = OPTIONS[index]

    pygame.draw.rect(surf, SET_ROW_SEL if selected else SET_ROW_BG, rect, border_radius=5)
    pygame.draw.rect(surf, INK, rect, 2 if selected else 1, border_radius=5)
    if selected:
        glow = pygame.Surface((rect.w - 6, rect.h // 2 - 2), pygame.SRCALPHA)
        glow.fill((255, 255, 255, 40))
        surf.blit(glow, (rect.x + 3, rect.y + 3))
        pygame.draw.circle(surf, INK, (rect.x + 14, rect.centery), 6)
        pygame.draw.circle(surf, MENU_CURSOR, (rect.x + 14, rect.centery), 4)

    text_color = PAPER if selected else SET_ROW_TEXT
    label = font(SM).render(option["label"], False, text_color)
    surf.blit(label, (rect.x + 26, rect.centery - label.get_height() // 2))

    left, value_box, right = _row_parts(rect)
    pygame.draw.rect(surf, SET_CHIP_BG, value_box, border_radius=4)
    pygame.draw.rect(surf, INK, value_box, 1, border_radius=4)
    glyph = font(SM).render(state.value_label(index), False, SET_ROW_TEXT)
    surf.blit(
        glyph,
        (value_box.centerx - glyph.get_width() // 2, value_box.centery - glyph.get_height() // 2),
    )

    count = len(option["values"])
    pick = state.value_index(index)
    _arrow(surf, left, True, selected and pick > 0)
    _arrow(surf, right, False, selected and pick < count - 1)


def _button(surf, index, rect, focused):
    label, action = BUTTONS[index]
    red = action == "back"
    surf.blit(frame("btn_frame_red.png" if red else "btn_frame_gold.png", rect.size), rect.topleft)

    if focused:
        glow = pygame.Surface((rect.w - 12, rect.h - 12), pygame.SRCALPHA)
        glow.fill((255, 255, 255, 46))
        surf.blit(glow, (rect.x + 6, rect.y + 6))

    color = PAPER if red else MENU_BTN_TEXT
    glyph = font(SM).render(label, False, color)
    pos = (rect.centerx - glyph.get_width() // 2, rect.centery - glyph.get_height() // 2)
    if red:
        surf.blit(font(SM).render(label, False, MENU_BTN_RED_SHADOW), (pos[0] + 1, pos[1] + 1))
    surf.blit(glyph, pos)

    if focused:
        cx, cy = rect.x + 14, rect.centery
        pygame.draw.circle(surf, INK, (cx, cy), 6)
        pygame.draw.circle(surf, PAPER if red else MENU_CURSOR, (cx, cy), 4)


def render_bottom(surf, state):
    from .menu_view import _pattern_surface

    surf.blit(_pattern_surface(), (0, 0))
    for i, rect in enumerate(ROW_RECTS):
        _row(surf, i, rect, state)
    for i, rect in enumerate(BUTTON_RECTS):
        _button(surf, i, rect, state.on_buttons and state.button == i)


def hit_test_rows(local):
    for i, rect in enumerate(ROW_RECTS):
        if rect.collidepoint(local):
            return i
    return None


def hit_test_arrows(local, row):
    left, value, right = _row_parts(ROW_RECTS[row])
    if left.collidepoint(local):
        return -1
    if right.collidepoint(local) or value.collidepoint(local):
        return 1
    return None


def hit_test_buttons(local):
    for i, rect in enumerate(BUTTON_RECTS):
        if rect.collidepoint(local):
            return i
    return None
