import pygame

from .analysis import BUTTONS, EXIT_BUTTON
from .board_view import DRAW_ORDER
from .draw import darken, diamond, draw_text
from .fonts import LG, SM, font
from .heatmap import heat_color
from .sprites import frame
from .theme import (
    ANALYSIS_BG,
    BTN_DIM_TEXT,
    BTN_GOLD_SHADOW,
    CELL_HIT,
    CELL_HIT_SIDE,
    CHART_POINT_HOT,
    INK,
    LAB_AXIS,
    LAB_BG,
    LAB_GRID,
    LAB_SCANLINE,
    LAB_TITLE,
    MAP_EMPTY,
    MAP_MISS,
    MENU_BTN_RED_SHADOW,
    MENU_BTN_TEXT,
    PAPER,
    SCREEN_H,
    SCREEN_W,
    SIDE_A,
    SIDE_B,
    TERM_BG,
    TERM_EDGE,
    TERM_HIGH,
    TERM_LABEL,
    TERM_TEXT,
    TERM_VALUE,
    TERM_WARN,
)

TITLE_Y = 12

PLOT_LEFT, PLOT_TOP, PLOT_RIGHT, PLOT_BOTTOM = 30, 45, 300, 215
PLOT_W = PLOT_RIGHT - PLOT_LEFT - 10
PLOT_H = PLOT_BOTTOM - PLOT_TOP

SIDE_COLORS = (SIDE_A, SIDE_B)

BAND_Y = (72, 118)
BAND_H = 18

FLEET_HEAD = (40, 122)
FLEET_ROW_H = 12
FLEET_ROW_GAP = 3
FLEET_X0 = 44

GRID_2D = 12
GRID_2D_Y = 66
GRID_2D_X = (26, 174)

ISO_ORIGINS = ((92, 62), (228, 128))
ISO_TILE_W, ISO_TILE_H = 14, 7

LEGEND_Y = 224

TAB_Y, TAB_H = 26, 12

TL_ISO_ORIGIN = (160, 68)
TL_TILE_W, TL_TILE_H = 22, 11
TL_LIFT = 14
TL_GRID = 13
TL_GRID_X, TL_GRID_Y = 95, 58
TL_RAMP = pygame.Rect(236, 190, 56, 6)
TL_BAR = pygame.Rect(PLOT_LEFT, 204, PLOT_W, 10)

TERM_H = 110
TERM_PAD = 12
TERM_LINE = 14
TERM_FIRST = 22

PANEL_TOP = TERM_H + 4
BTN_COLS, BTN_ROWS = 3, 2
BTN_GAP = 10
BTN_W = (SCREEN_W - TERM_PAD * 2 - BTN_GAP * (BTN_COLS - 1)) // BTN_COLS
BTN_H = (SCREEN_H - PANEL_TOP - TERM_PAD * 2 - BTN_GAP) // BTN_ROWS

BUTTON_RECTS = [
    pygame.Rect(
        TERM_PAD + (i % BTN_COLS) * (BTN_W + BTN_GAP),
        PANEL_TOP + TERM_PAD + (i // BTN_COLS) * (BTN_H + BTN_GAP),
        BTN_W,
        BTN_H,
    )
    for i in range(len(BUTTONS))
]

TERM_COLORS = {
    "label": TERM_LABEL,
    "val": TERM_VALUE,
    "high": TERM_HIGH,
    "warn": TERM_WARN,
    "text": TERM_TEXT,
}

_lab = None
_scan = None


def _lab_surface():
    global _lab
    if _lab is None:
        _lab = pygame.Surface((SCREEN_W, SCREEN_H))
        _lab.fill(LAB_BG)
        for x in range(0, SCREEN_W, 20):
            pygame.draw.line(_lab, LAB_GRID, (x, 0), (x, SCREEN_H))
        for y in range(0, SCREEN_H, 20):
            pygame.draw.line(_lab, LAB_GRID, (0, y), (SCREEN_W, y))
    return _lab


def _scan_surface():
    global _scan
    if _scan is None:
        _scan = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        for y in range(0, SCREEN_H, 2):
            pygame.draw.line(_scan, (0, 0, 0, LAB_SCANLINE), (0, y), (SCREEN_W, y))
    return _scan


def _tag(surf, text, color, pos):
    glyph = font(SM).render(text, False, color)
    box = pygame.Rect(pos[0] - 2, pos[1] - 1, glyph.get_width() + 4, glyph.get_height() + 2)
    pygame.draw.rect(surf, LAB_BG, box)
    surf.blit(glyph, pos)


def _axes(surf, x_label, y_label=None):
    pygame.draw.line(surf, LAB_AXIS, (PLOT_LEFT, PLOT_BOTTOM), (PLOT_RIGHT, PLOT_BOTTOM), 2)
    pygame.draw.line(surf, LAB_AXIS, (PLOT_LEFT, PLOT_TOP), (PLOT_LEFT, PLOT_BOTTOM), 2)
    label = font(SM).render(x_label, False, LAB_AXIS)
    surf.blit(label, (PLOT_RIGHT - label.get_width(), PLOT_BOTTOM + 8))
    if y_label:
        _tag(surf, y_label, LAB_AXIS, (PLOT_LEFT + 5, PLOT_TOP + 2))


def _legend(surf, items, y):
    x = PLOT_RIGHT - 96
    for color, text in items:
        pygame.draw.rect(surf, color, pygame.Rect(x, y + 1, 8, 6))
        draw_text(surf, text, font(SM), color, (x + 12, y))
        y += 11


def _no_data(surf):
    msg = font(LG).render("BRAK PARTII", False, LAB_TITLE)
    surf.blit(msg, msg.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2 - 12)))
    hint = font(SM).render("Rozegraj gre i wroc tutaj", False, LAB_AXIS)
    surf.blit(hint, hint.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2 + 14)))


def _shot_x(index, count):
    if count <= 1:
        return PLOT_LEFT + 10
    return PLOT_LEFT + 10 + index * PLOT_W / (count - 1)


def _render_accuracy(surf, analysis):
    report = analysis.report
    _axes(surf, "Strzal")
    count = report.longest

    for pct in (0.25, 0.5, 0.75):
        y = PLOT_BOTTOM - pct * PLOT_H
        for x in range(PLOT_LEFT, PLOT_RIGHT, 6):
            pygame.draw.line(surf, LAB_GRID, (x, y), (x + 3, y))
    draw_text(surf, "100", font(SM), LAB_AXIS, (PLOT_LEFT - 26, PLOT_TOP - 2))
    draw_text(surf, "50", font(SM), LAB_AXIS, (PLOT_LEFT - 26, PLOT_BOTTOM - PLOT_H // 2 - 4))
    draw_text(surf, "0", font(SM), LAB_AXIS, (PLOT_LEFT - 26, PLOT_BOTTOM - 8))

    for side_index, side in enumerate(report.sides):
        if len(side.cum) < 2:
            continue
        color = SIDE_COLORS[side_index]
        points = [
            (_shot_x(i, count), PLOT_BOTTOM - value * PLOT_H) for i, value in enumerate(side.cum)
        ]
        pygame.draw.lines(surf, color, False, points, 2)

    _legend(
        surf,
        [
            (SIDE_COLORS[i], f"{s.name} {s.accuracy * 100:.0f}%")
            for i, s in enumerate(report.sides)
        ],
        PLOT_TOP + 4,
    )

    for step in range(0, count, 10):
        x = _shot_x(step, count)
        if x > PLOT_RIGHT - 60:
            break
        label = font(SM).render(str(step + 1), False, LAB_AXIS)
        surf.blit(label, (x - label.get_width() // 2, PLOT_BOTTOM + 6))

    if analysis.hover and analysis.hover[0] == "turn":
        index = analysis.hover[1]
        x = _shot_x(index, count)
        for y in range(PLOT_TOP, PLOT_BOTTOM, 4):
            pygame.draw.line(surf, LAB_AXIS, (x, y), (x, y + 2))
        for side_index, side in enumerate(report.sides):
            if index < len(side.cum):
                y = PLOT_BOTTOM - side.cum[index] * PLOT_H
                pygame.draw.circle(surf, SIDE_COLORS[side_index], (int(x), int(y)), 4)
                pygame.draw.circle(surf, PAPER, (int(x), int(y)), 4, 1)


def _shot_color(entry):
    if entry["res"] == "M":
        return MAP_MISS
    if entry["res"] == "S":
        return CELL_HIT_SIDE
    return CELL_HIT


def _render_timeline(surf, analysis):
    report = analysis.report
    count = max(1, report.longest)
    cell_w = max(2.0, PLOT_W / count)

    for side_index, side in enumerate(report.sides):
        y = BAND_Y[side_index]
        draw_text(surf, side.name, font(SM), SIDE_COLORS[side_index], (PLOT_LEFT, y - 12))
        pygame.draw.rect(
            surf, LAB_GRID, pygame.Rect(PLOT_LEFT - 1, y - 1, int(PLOT_W) + 2, BAND_H + 2), 1
        )
        for i, entry in enumerate(side.shots):
            x = PLOT_LEFT + i * cell_w
            rect = pygame.Rect(int(x), y, max(1, int(cell_w) - 1), BAND_H)
            pygame.draw.rect(surf, _shot_color(entry), rect)
            if entry["sunk"] is not None:
                pygame.draw.rect(surf, TERM_HIGH, rect, 1)
        hover = analysis.hover
        if hover and hover[0] == "shot" and hover[1] == side_index:
            x = PLOT_LEFT + hover[2] * cell_w
            pygame.draw.rect(
                surf, PAPER, pygame.Rect(int(x) - 1, y - 2, max(3, int(cell_w) + 1), BAND_H + 4), 1
            )

    draw_text(surf, f"strzalow: {report.total}", font(SM), LAB_AXIS, (PLOT_LEFT, 158))
    _legend(
        surf,
        [(CELL_HIT, "TRAFIENIE"), (CELL_HIT_SIDE, "ZATOPIONY"), (MAP_MISS, "PUDLO")],
        170,
    )


def _fleet_rows(analysis):
    rows = []
    for side_index, side in enumerate(analysis.report.sides):
        top = FLEET_HEAD[side_index] + 10
        for k in range(len(side.fleet)):
            rows.append((side_index, k, top + k * (FLEET_ROW_H + FLEET_ROW_GAP)))
    return rows


def _render_fleet(surf, analysis):
    report = analysis.report
    span = max(1, report.longest)
    width = PLOT_RIGHT - FLEET_X0

    for side_index, side in enumerate(report.sides):
        head = FLEET_HEAD[side_index]
        draw_text(
            surf,
            f"{side.name}  {side.sunk}/5",
            font(SM),
            SIDE_COLORS[side_index],
            (PLOT_LEFT, head),
        )

    for side_index, ship_index, y in _fleet_rows(analysis):
        side = report.sides[side_index]
        size, shot = side.fleet[ship_index]
        color = SIDE_COLORS[side_index]
        draw_text(surf, str(size), font(SM), LAB_AXIS, (PLOT_LEFT + 8, y + 2))
        pygame.draw.rect(surf, LAB_GRID, pygame.Rect(FLEET_X0, y, width, FLEET_ROW_H), 1)
        if shot is None:
            pygame.draw.rect(surf, darken(color, 0.35), pygame.Rect(FLEET_X0, y, width, FLEET_ROW_H))
            draw_text(surf, "X", font(SM), PAPER, (PLOT_RIGHT - 12, y + 2))
        else:
            bar = max(3, int(width * shot / span))
            pygame.draw.rect(surf, color, pygame.Rect(FLEET_X0, y, bar, FLEET_ROW_H))
            label = font(SM).render(str(shot), False, PAPER if bar > 24 else LAB_AXIS)
            surf.blit(label, (FLEET_X0 + bar - label.get_width() - 3 if bar > 24 else FLEET_X0 + bar + 3, y + 2))
        hover = analysis.hover
        if hover and hover[0] == "ship" and hover[1] == side_index and hover[2] == ship_index:
            pygame.draw.rect(surf, PAPER, pygame.Rect(FLEET_X0 - 1, y - 1, width + 2, FLEET_ROW_H + 2), 1)

    draw_text(surf, f"strzal 1..{span}", font(SM), LAB_AXIS, (FLEET_X0, 206))


def _cell_color(side, index):
    entry = side.board.get(index)
    return MAP_EMPTY if entry is None else _shot_color(entry)


def _iso_center(col, row, origin):
    ox, oy = origin
    return ox + (col - row) * (ISO_TILE_W / 2), oy + (col + row) * (ISO_TILE_H / 2)


def _render_map_iso(surf, analysis):
    hover = analysis.hover
    for side_index, side in enumerate(analysis.report.sides):
        origin = ISO_ORIGINS[side_index]
        label = font(SM).render(side.name, False, SIDE_COLORS[side_index])
        surf.blit(label, (origin[0] - label.get_width() // 2, origin[1] - 20))
        for i in DRAW_ORDER:
            entry = side.board.get(i)
            color = _cell_color(side, i)
            lift = 0 if entry is None else (4 if entry["res"] != "M" else 1)
            cx, cy = _iso_center(i % 10, i // 10, origin)
            top = cy - lift
            if lift:
                pygame.draw.polygon(
                    surf,
                    darken(color, 0.6),
                    [
                        (cx - ISO_TILE_W / 2, cy),
                        (cx, cy + ISO_TILE_H / 2),
                        (cx, cy + ISO_TILE_H / 2 - lift),
                        (cx - ISO_TILE_W / 2, cy - lift),
                    ],
                )
                pygame.draw.polygon(
                    surf,
                    darken(color, 0.8),
                    [
                        (cx + ISO_TILE_W / 2, cy),
                        (cx, cy + ISO_TILE_H / 2),
                        (cx, cy + ISO_TILE_H / 2 - lift),
                        (cx + ISO_TILE_W / 2, cy - lift),
                    ],
                )
            shape = diamond(cx, top, ISO_TILE_W, ISO_TILE_H)
            pygame.draw.polygon(surf, color, shape)
            pygame.draw.polygon(surf, darken(color, 0.7), shape, 1)
            if hover and hover[0] == "cell" and hover[1] == side_index and hover[2] == i:
                pygame.draw.polygon(surf, PAPER, shape, 2)


def _render_map_2d(surf, analysis):
    hover = analysis.hover
    for side_index, side in enumerate(analysis.report.sides):
        ox = GRID_2D_X[side_index]
        label = font(SM).render(side.name, False, SIDE_COLORS[side_index])
        surf.blit(label, (ox + 60 - label.get_width() // 2, GRID_2D_Y - 14))
        for i in range(100):
            x = ox + (i % 10) * GRID_2D
            y = GRID_2D_Y + (i // 10) * GRID_2D
            rect = pygame.Rect(x, y, GRID_2D - 1, GRID_2D - 1)
            pygame.draw.rect(surf, _cell_color(side, i), rect)
            if hover and hover[0] == "cell" and hover[1] == side_index and hover[2] == i:
                pygame.draw.rect(surf, PAPER, rect, 2)


def _render_map(surf, analysis):
    if analysis.iso:
        _render_map_iso(surf, analysis)
    else:
        _render_map_2d(surf, analysis)
    _legend(
        surf,
        [(CELL_HIT, "TRAFIENIE"), (CELL_HIT_SIDE, "ZATOPIONY"), (MAP_MISS, "PUDLO")],
        LEGEND_Y - 24,
    )


def tabs(analysis):
    if not analysis.has_tabs():
        return []
    out = []
    x = PLOT_RIGHT
    for label, iso in (("2D", False), ("ISO", True)):
        width = font(SM).size(label)[0] + 10
        x -= width
        out.append((pygame.Rect(x, TAB_Y, width, TAB_H), label, analysis.iso == iso, ("iso", iso)))
        x -= 4
    if analysis.view == "timelapse":
        x = PLOT_LEFT
        for i, side in enumerate(analysis.report.sides):
            width = font(SM).size(side.name)[0] + 10
            out.append(
                (pygame.Rect(x, TAB_Y, width, TAB_H), side.name, analysis.tl_side == i, ("side", i))
            )
            x += width + 4
    return out


def _render_tabs(surf, analysis):
    for rect, label, active, _ in tabs(analysis):
        pygame.draw.rect(surf, LAB_TITLE if active else LAB_BG, rect)
        pygame.draw.rect(surf, LAB_TITLE if active else LAB_AXIS, rect, 1)
        glyph = font(SM).render(label, False, INK if active else LAB_AXIS)
        surf.blit(glyph, (rect.centerx - glyph.get_width() // 2, rect.y + 2))


def _tl_cell_lift(value):
    return int(value * TL_LIFT)


def _render_timelapse(surf, analysis):
    side = analysis.report.sides[analysis.tl_side]
    frame_no = min(analysis.frame, len(side.shots))
    density = side.density_at(frame_no)
    search = side.search_at(frame_no)
    last = side.shots[frame_no - 1]["idx"] if frame_no else None

    if analysis.iso:
        for i in DRAW_ORDER:
            cx, cy = _tl_center(i % 10, i // 10)
            color, lift = _tl_look(search[i], density[i])
            top = cy - lift
            if lift:
                pygame.draw.polygon(
                    surf,
                    darken(color, 0.6),
                    [
                        (cx - TL_TILE_W / 2, cy),
                        (cx, cy + TL_TILE_H / 2),
                        (cx, cy + TL_TILE_H / 2 - lift),
                        (cx - TL_TILE_W / 2, cy - lift),
                    ],
                )
                pygame.draw.polygon(
                    surf,
                    darken(color, 0.8),
                    [
                        (cx + TL_TILE_W / 2, cy),
                        (cx, cy + TL_TILE_H / 2),
                        (cx, cy + TL_TILE_H / 2 - lift),
                        (cx + TL_TILE_W / 2, cy - lift),
                    ],
                )
            shape = diamond(cx, top, TL_TILE_W, TL_TILE_H)
            pygame.draw.polygon(surf, color, shape)
            pygame.draw.polygon(surf, darken(color, 0.7), shape, 1)
            if i == last:
                pygame.draw.polygon(surf, PAPER, shape, 2)
    else:
        for i in range(100):
            x = TL_GRID_X + (i % 10) * TL_GRID
            y = TL_GRID_Y + (i // 10) * TL_GRID
            rect = pygame.Rect(x, y, TL_GRID - 1, TL_GRID - 1)
            color, _ = _tl_look(search[i], density[i])
            pygame.draw.rect(surf, color, rect)
            if i == last:
                pygame.draw.rect(surf, PAPER, rect, 2)

    for x in range(TL_RAMP.w):
        pygame.draw.line(
            surf,
            heat_color(x / max(1, TL_RAMP.w - 1)),
            (TL_RAMP.x + x, TL_RAMP.y),
            (TL_RAMP.x + x, TL_RAMP.bottom),
        )
    pygame.draw.rect(surf, LAB_AXIS, TL_RAMP, 1)
    draw_text(surf, "density", font(SM), LAB_AXIS, (TL_RAMP.x - 60, TL_RAMP.y - 1))

    total = max(1, len(side.shots))
    step = TL_BAR.w / total
    pygame.draw.rect(surf, LAB_GRID, TL_BAR, 1)
    for i, entry in enumerate(side.shots):
        rect = pygame.Rect(int(TL_BAR.x + i * step), TL_BAR.y, max(1, int(step)), TL_BAR.h)
        color = _shot_color(entry)
        pygame.draw.rect(surf, color if i < frame_no else darken(color, 0.3), rect)
    marker = int(TL_BAR.x + min(frame_no, total) * step)
    pygame.draw.line(surf, PAPER, (marker, TL_BAR.y - 3), (marker, TL_BAR.bottom + 3), 2)
    draw_text(surf, f"{frame_no}/{total}", font(SM), LAB_AXIS, (TL_BAR.x, TL_BAR.bottom + 6))


def _tl_center(col, row):
    ox, oy = TL_ISO_ORIGIN
    return ox + (col - row) * (TL_TILE_W / 2), oy + (col + row) * (TL_TILE_H / 2)


def _tl_look(state, value):
    if state == "M":
        return MAP_MISS, 1
    if state == "S":
        return CELL_HIT_SIDE, 5
    if state == "H":
        return CELL_HIT, 5
    return heat_color(value), _tl_cell_lift(value)


RENDERERS = {
    "accuracy": _render_accuracy,
    "timeline": _render_timeline,
    "fleet": _render_fleet,
    "map": _render_map,
    "timelapse": _render_timelapse,
}


def render_top(surf, analysis):
    surf.blit(_lab_surface(), (0, 0))
    title = font(SM).render(analysis.title, False, LAB_TITLE)
    pos = ((SCREEN_W - title.get_width()) // 2, TITLE_Y)
    surf.blit(font(SM).render(analysis.title, False, INK), (pos[0] + 2, pos[1] + 2))
    surf.blit(title, pos)

    if analysis.has_data:
        RENDERERS[analysis.view](surf, analysis)
        _render_tabs(surf, analysis)
    else:
        _no_data(surf)
    surf.blit(_scan_surface(), (0, 0))


def _terminal(surf, analysis):
    pygame.draw.rect(surf, TERM_BG, pygame.Rect(0, 0, SCREEN_W, TERM_H))
    pygame.draw.rect(surf, TERM_EDGE, pygame.Rect(0, TERM_H, SCREEN_W, 4))

    label = font(SM).render("DANE SZCZEGOLOWE", False, PAPER)
    tab = pygame.Rect(SCREEN_W - label.get_width() - 16, 0, label.get_width() + 16, 18)
    pygame.draw.rect(surf, TERM_EDGE, tab, border_bottom_left_radius=8)
    surf.blit(label, (tab.x + 8, 5))

    y = TERM_FIRST
    for line in analysis.terminal_lines():
        x = TERM_PAD
        for text, key in line:
            color = TERM_COLORS.get(key, TERM_TEXT)
            surf.blit(font(SM).render(text, False, (0, 0, 0)), (x + 1, y + 1))
            x = draw_text(surf, text, font(SM), color, (x, y)).right
        y += TERM_LINE


def _button(surf, analysis, index, rect):
    head, sub = analysis.button_label(index)
    active = analysis.button_active(index)
    red = index == EXIT_BUTTON

    if red:
        sprite_name = "btn_frame_red.png"
    elif active:
        sprite_name = "btn_frame_gold.png"
    else:
        sprite_name = "btn_frame.png"
    surf.blit(frame(sprite_name, rect.size), rect.topleft)

    if index == analysis.selected:
        glow = pygame.Surface((rect.w - 12, rect.h - 12), pygame.SRCALPHA)
        glow.fill((255, 255, 255, 46))
        surf.blit(glow, (rect.x + 6, rect.y + 6))

    if red:
        color, shadow = PAPER, MENU_BTN_RED_SHADOW
    elif active:
        color, shadow = INK, BTN_GOLD_SHADOW
    elif analysis.has_data:
        color, shadow = MENU_BTN_TEXT, None
    else:
        color, shadow = BTN_DIM_TEXT, None

    lines = [head] if sub is None else [head, sub]
    y = rect.centery - (len(lines) * 10 - 2) // 2
    for text in lines:
        glyph = font(SM).render(text, False, color)
        x = rect.centerx - glyph.get_width() // 2
        if shadow is not None:
            surf.blit(font(SM).render(text, False, shadow), (x + 1, y + 1))
        surf.blit(glyph, (x, y))
        y += 10

    if index == analysis.selected:
        cx, cy = rect.x + 12, rect.bottom - 10
        pygame.draw.circle(surf, INK, (cx, cy), 5)
        pygame.draw.circle(surf, PAPER if red else CHART_POINT_HOT, (cx, cy), 3)


def render_bottom(surf, analysis):
    surf.fill(ANALYSIS_BG)
    _terminal(surf, analysis)
    for i, rect in enumerate(BUTTON_RECTS):
        _button(surf, analysis, i, rect)


def hit_test_buttons(local):
    for i, rect in enumerate(BUTTON_RECTS):
        if rect.collidepoint(local):
            return i
    return None


def hit_test_tabs(analysis, local):
    for rect, _, _, action in tabs(analysis):
        if rect.collidepoint(local):
            return action
    return None


def hit_test_view(analysis, local):
    if not analysis.has_data:
        return None
    x, y = local
    if analysis.view == "accuracy":
        return _hit_accuracy(analysis, x, y)
    if analysis.view == "timeline":
        return _hit_timeline(analysis, x, y)
    if analysis.view == "fleet":
        return _hit_fleet(analysis, x, y)
    if analysis.view == "timelapse":
        return _hit_timelapse(analysis, x, y)
    return _hit_map_iso(analysis, x, y) if analysis.iso else _hit_map_2d(analysis, x, y)


def _hit_timelapse(analysis, x, y):
    if not (TL_BAR.y - 4 <= y <= TL_BAR.bottom + 4 and TL_BAR.x <= x <= TL_BAR.right):
        return None
    total = max(1, len(analysis.report.sides[analysis.tl_side].shots))
    index = int(round((x - TL_BAR.x) / TL_BAR.w * total))
    return ("frame", max(0, min(total, index)))


def _hit_accuracy(analysis, x, y):
    if not (PLOT_TOP <= y <= PLOT_BOTTOM and PLOT_LEFT <= x <= PLOT_RIGHT):
        return None
    count = analysis.report.longest
    if count <= 1:
        return ("turn", 0)
    index = int(round((x - PLOT_LEFT - 10) * (count - 1) / PLOT_W))
    return ("turn", max(0, min(count - 1, index)))


def _hit_timeline(analysis, x, y):
    count = max(1, analysis.report.longest)
    cell_w = max(2.0, PLOT_W / count)
    for side_index, side in enumerate(analysis.report.sides):
        top = BAND_Y[side_index]
        if top <= y <= top + BAND_H and PLOT_LEFT <= x <= PLOT_LEFT + PLOT_W:
            index = int((x - PLOT_LEFT) // cell_w)
            if 0 <= index < len(side.shots):
                return ("shot", side_index, index)
    return None


def _hit_fleet(analysis, x, y):
    if not (PLOT_LEFT <= x <= PLOT_RIGHT):
        return None
    for side_index, ship_index, row_y in _fleet_rows(analysis):
        if row_y <= y <= row_y + FLEET_ROW_H:
            return ("ship", side_index, ship_index)
    return None


def _hit_map_2d(analysis, x, y):
    for side_index in (0, 1):
        ox = GRID_2D_X[side_index]
        col = (x - ox) // GRID_2D
        row = (y - GRID_2D_Y) // GRID_2D
        if 0 <= col < 10 and 0 <= row < 10:
            return ("cell", side_index, int(row) * 10 + int(col))
    return None


def _hit_map_iso(analysis, x, y):
    for side_index in (0, 1):
        origin = ISO_ORIGINS[side_index]
        side = analysis.report.sides[side_index]
        for i in reversed(DRAW_ORDER):
            entry = side.board.get(i)
            lift = 0 if entry is None else (4 if entry["res"] != "M" else 1)
            cx, cy = _iso_center(i % 10, i // 10, origin)
            dx = abs(x - cx) / (ISO_TILE_W / 2)
            dy = abs(y - (cy - lift)) / (ISO_TILE_H / 2)
            if dx + dy <= 1.05:
                return ("cell", side_index, i)
    return None
