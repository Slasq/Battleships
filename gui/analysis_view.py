import pygame

from .analysis import (
    AVG_DQN,
    AVG_HEURISTIC,
    BUTTONS,
    EPISODES,
    EXIT_BUTTON,
    HIST_MIN,
    HIST_STEP,
    TOGGLE_BUTTON,
)
from .board_view import DRAW_ORDER
from .draw import darken, diamond, draw_text
from .fonts import SM, font
from .heatmap import heat_color
from .sprites import frame
from .theme import (
    ANALYSIS_BG,
    BTN_DIM_TEXT,
    BTN_GOLD_SHADOW,
    CHART_BAR,
    CHART_BAR_HOT,
    CHART_GUIDE,
    CHART_LINE,
    CHART_LINE_ALT,
    CHART_POINT,
    CHART_POINT_HOT,
    INK,
    LAB_AXIS,
    LAB_BG,
    LAB_GRID,
    LAB_SCANLINE,
    LAB_TITLE,
    MENU_BTN_RED_SHADOW,
    MENU_BTN_TEXT,
    PAPER,
    SCREEN_H,
    SCREEN_W,
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
POINT_X0, POINT_W = 40, 260
BASE_Y, PLOT_H = 205, 160

LOSS_MAX = 3.0
REWARD_MIN, REWARD_MAX = -60.0, 80.0

BARS = 14
BAR_SPAN = POINT_W / BARS

GRID_2D_X, GRID_2D_Y = 71, 44
CELL, CELL_GAP = 16, 2

ISO_ORIGIN = (160, 62)
ISO_TILE_W, ISO_TILE_H = 24, 12
ISO_LIFT = 16

LEGEND = pygame.Rect(96, 222, 128, 8)

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


def point_x(index):
    return POINT_X0 + index * (POINT_W / (EPISODES - 1))


def _loss_y(value):
    return BASE_Y - (value / LOSS_MAX) * PLOT_H


def _reward_y(value):
    return BASE_Y - ((value - REWARD_MIN) / (REWARD_MAX - REWARD_MIN)) * PLOT_H


def _eps_y(value):
    return BASE_Y - value * PLOT_H


def _axes(surf, x_label, y_label, y_right=None):
    pygame.draw.line(surf, LAB_AXIS, (PLOT_LEFT, PLOT_BOTTOM), (PLOT_RIGHT, PLOT_BOTTOM), 2)
    pygame.draw.line(surf, LAB_AXIS, (PLOT_LEFT, PLOT_TOP), (PLOT_LEFT, PLOT_BOTTOM), 2)
    label = font(SM).render(x_label, False, LAB_AXIS)
    surf.blit(label, (PLOT_RIGHT - label.get_width(), PLOT_BOTTOM + 8))
    _tag(surf, y_label, LAB_AXIS, (PLOT_LEFT + 5, PLOT_TOP + 2))
    if y_right:
        width = font(SM).size(y_right)[0]
        _tag(surf, y_right, CHART_LINE_ALT, (PLOT_RIGHT - width, PLOT_TOP + 2))


def _tag(surf, text, color, pos):
    glyph = font(SM).render(text, False, color)
    pygame.draw.rect(surf, LAB_BG, pygame.Rect(pos[0] - 2, pos[1] - 1, glyph.get_width() + 4, glyph.get_height() + 2))
    surf.blit(glyph, pos)


def _hover_marker(surf, x, y, color):
    for step in range(PLOT_TOP, PLOT_BOTTOM, 4):
        pygame.draw.line(surf, CHART_GUIDE, (x, step), (x, step + 2))
    pygame.draw.circle(surf, color, (int(x), int(y)), 5)


def _epoch_ticks(surf, series):
    for i in range(0, EPISODES - 3, 3):
        label = font(SM).render(str(series[i]["ep"]), False, LAB_AXIS)
        surf.blit(label, (point_x(i) - label.get_width() // 2, PLOT_BOTTOM + 6))


def _line_chart(surf, data, to_y, color, hover):
    points = [(point_x(i), to_y(v)) for i, v in enumerate(data)]
    pygame.draw.lines(surf, color, False, points, 2)
    for i, (x, y) in enumerate(points):
        if i != hover:
            pygame.draw.circle(surf, CHART_POINT, (int(x), int(y)), 3)
    return points


def _render_loss(surf, analysis):
    _axes(surf, "Epoka", "Loss")
    data = [d["loss"] for d in analysis.series]
    points = _line_chart(surf, data, _loss_y, CHART_LINE, analysis.hover)
    _epoch_ticks(surf, analysis.series)
    draw_text(surf, f"{LOSS_MAX:.1f}", font(SM), LAB_AXIS, (PLOT_LEFT - 26, PLOT_TOP + 2))
    draw_text(surf, "0.0", font(SM), LAB_AXIS, (PLOT_LEFT - 26, BASE_Y - 4))
    if analysis.hover is not None:
        x, y = points[analysis.hover]
        _hover_marker(surf, x, y, CHART_POINT_HOT)


def _render_reward(surf, analysis):
    _axes(surf, "Epoka", "Reward", "Eps")
    rewards = [d["reward"] for d in analysis.series]
    eps = [d["epsilon"] for d in analysis.series]

    zero_y = _reward_y(0)
    for step in range(PLOT_LEFT, PLOT_RIGHT, 6):
        pygame.draw.line(surf, CHART_GUIDE, (step, zero_y), (step + 3, zero_y))

    eps_points = [(point_x(i), _eps_y(v)) for i, v in enumerate(eps)]
    pygame.draw.lines(surf, CHART_LINE_ALT, False, eps_points, 1)
    points = _line_chart(surf, rewards, _reward_y, CHART_LINE, analysis.hover)
    _epoch_ticks(surf, analysis.series)
    draw_text(surf, "0", font(SM), LAB_AXIS, (PLOT_LEFT - 12, zero_y - 4))
    if analysis.hover is not None:
        x, y = points[analysis.hover]
        _hover_marker(surf, x, y, CHART_POINT_HOT)


def _render_shots(surf, analysis):
    _axes(surf, "Strzaly", "Partie")
    top = max(analysis.hist)
    for i, count in enumerate(analysis.hist):
        h = int((count / top) * (PLOT_H - 10))
        x = int(POINT_X0 - BAR_SPAN / 2 + i * BAR_SPAN)
        rect = pygame.Rect(x, PLOT_BOTTOM - h, int(BAR_SPAN) - 2, h)
        hot = i == analysis.hover
        pygame.draw.rect(surf, CHART_BAR_HOT if hot else CHART_BAR, rect)
        pygame.draw.rect(surf, LAB_AXIS if hot else CHART_BAR, rect, 1)
        if i % 3 == 0 and i <= 9:
            label = font(SM).render(str(HIST_MIN + i * HIST_STEP), False, LAB_AXIS)
            surf.blit(label, (rect.centerx - label.get_width() // 2, PLOT_BOTTOM + 6))

    legend_y = PLOT_TOP + 6
    for value, color, name in (
        (AVG_DQN, CHART_LINE, "DQN"),
        (AVG_HEURISTIC, CHART_POINT, "HEUR"),
    ):
        x = POINT_X0 - BAR_SPAN / 2 + (value - HIST_MIN) / HIST_STEP * BAR_SPAN
        for step in range(PLOT_TOP, PLOT_BOTTOM, 4):
            pygame.draw.line(surf, color, (x, step), (x, step + 2))
        pygame.draw.line(surf, color, (PLOT_RIGHT - 92, legend_y + 4), (PLOT_RIGHT - 82, legend_y + 4), 2)
        draw_text(surf, f"{name} {value:.1f}", font(SM), color, (PLOT_RIGHT - 78, legend_y))
        legend_y += 12


def _render_heat_2d(surf, analysis):
    for i, value in enumerate(analysis.heat):
        col, row = i % 10, i // 10
        x = GRID_2D_X + col * (CELL + CELL_GAP)
        y = GRID_2D_Y + row * (CELL + CELL_GAP)
        pygame.draw.rect(surf, (0, 0, 0), pygame.Rect(x - 1, y + 1, CELL, CELL))
        pygame.draw.rect(surf, heat_color(value), pygame.Rect(x, y, CELL, CELL))
        if i == analysis.hover:
            pygame.draw.rect(surf, PAPER, pygame.Rect(x, y, CELL, CELL), 2)


def _iso_center(col, row):
    ox, oy = ISO_ORIGIN
    return ox + (col - row) * (ISO_TILE_W / 2), oy + (col + row) * (ISO_TILE_H / 2)


def _iso_cell(surf, cx, cy, fill, lift, outline=None):
    top = cy - lift
    if lift > 0:
        side = darken(fill, 0.7)
        pygame.draw.polygon(
            surf,
            darken(side, 0.8),
            [
                (cx - ISO_TILE_W / 2, cy),
                (cx, cy + ISO_TILE_H / 2),
                (cx, cy + ISO_TILE_H / 2 - lift),
                (cx - ISO_TILE_W / 2, cy - lift),
            ],
        )
        pygame.draw.polygon(
            surf,
            side,
            [
                (cx + ISO_TILE_W / 2, cy),
                (cx, cy + ISO_TILE_H / 2),
                (cx, cy + ISO_TILE_H / 2 - lift),
                (cx + ISO_TILE_W / 2, cy - lift),
            ],
        )
    shape = diamond(cx, top, ISO_TILE_W, ISO_TILE_H)
    pygame.draw.polygon(surf, fill, shape)
    pygame.draw.polygon(surf, darken(fill, 0.72), shape, 1)
    if outline:
        pygame.draw.polygon(surf, outline, shape, 2)


def _render_heat_iso(surf, analysis):
    for i in DRAW_ORDER:
        value = analysis.heat[i]
        cx, cy = _iso_center(i % 10, i // 10)
        _iso_cell(
            surf,
            cx,
            cy,
            heat_color(value),
            int(value * ISO_LIFT),
            PAPER if i == analysis.hover else None,
        )


def _legend(surf):
    for x in range(LEGEND.w):
        color = heat_color(x / max(1, LEGEND.w - 1))
        pygame.draw.line(surf, color, (LEGEND.x + x, LEGEND.y), (LEGEND.x + x, LEGEND.bottom))
    pygame.draw.rect(surf, LAB_AXIS, LEGEND, 1)
    small = font(SM)
    low = small.render("0.0", False, LAB_AXIS)
    high = small.render("1.0", False, LAB_AXIS)
    surf.blit(low, (LEGEND.x - low.get_width() - 4, LEGEND.y))
    surf.blit(high, (LEGEND.right + 4, LEGEND.y))


def _render_heatmap(surf, analysis):
    if analysis.iso:
        _render_heat_iso(surf, analysis)
    else:
        _render_heat_2d(surf, analysis)
    _legend(surf)


RENDERERS = {
    "loss": _render_loss,
    "reward": _render_reward,
    "shots": _render_shots,
    "heatmap": _render_heatmap,
}


def render_top(surf, analysis):
    surf.blit(_lab_surface(), (0, 0))
    title = font(SM).render(analysis.title, False, LAB_TITLE)
    pos = ((SCREEN_W - title.get_width()) // 2, TITLE_Y)
    shadow = font(SM).render(analysis.title, False, INK)
    surf.blit(shadow, (pos[0] + 2, pos[1] + 2))
    surf.blit(title, pos)

    RENDERERS[analysis.view](surf, analysis)
    surf.blit(_scan_surface(), (0, 0))


def _terminal(surf, analysis):
    box = pygame.Rect(0, 0, SCREEN_W, TERM_H)
    pygame.draw.rect(surf, TERM_BG, box)
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
            shadow = font(SM).render(text, False, (0, 0, 0))
            surf.blit(shadow, (x + 1, y + 1))
            rect = draw_text(surf, text, font(SM), color, (x, y))
            x = rect.right
        y += TERM_LINE


def _button(surf, analysis, index, rect):
    head, sub = analysis.button_label(index)
    active = analysis.button_active(index)
    red = index == EXIT_BUTTON
    enabled = analysis.button_enabled(index)

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
    elif enabled:
        color, shadow = MENU_BTN_TEXT, None
    else:
        color, shadow = BTN_DIM_TEXT, None

    lines = [head] if sub is None else [head, sub]
    total = len(lines) * 10 - 2
    y = rect.centery - total // 2
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


def hit_test_view(analysis, local):
    x, y = local
    if analysis.view == "heatmap":
        return _hit_heat_iso(analysis, x, y) if analysis.iso else _hit_heat_2d(x, y)
    if not (PLOT_TOP <= y <= PLOT_BOTTOM and PLOT_LEFT <= x <= PLOT_RIGHT):
        return None
    if analysis.view == "shots":
        index = int((x - POINT_X0 + BAR_SPAN / 2) // BAR_SPAN)
        return index if 0 <= index < BARS else None
    index = int(round((x - POINT_X0) / (POINT_W / (EPISODES - 1))))
    return index if 0 <= index < EPISODES else None


def _hit_heat_2d(x, y):
    col = (x - GRID_2D_X) // (CELL + CELL_GAP)
    row = (y - GRID_2D_Y) // (CELL + CELL_GAP)
    if 0 <= col < 10 and 0 <= row < 10:
        return int(row) * 10 + int(col)
    return None


def _hit_heat_iso(analysis, x, y):
    for i in reversed(DRAW_ORDER):
        lift = int(analysis.heat[i] * ISO_LIFT)
        cx, cy = _iso_center(i % 10, i // 10)
        dx = abs(x - cx) / (ISO_TILE_W / 2)
        dy = abs(y - (cy - lift)) / (ISO_TILE_H / 2)
        if dx + dy <= 1.05:
            return i
    return None
