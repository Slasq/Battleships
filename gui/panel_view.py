import pygame

from . import overlay
from .draw import draw_text, draw_text_in, wrap_text
from .fonts import MD, SM, font
from .match import Match
from .theme import (
    ATK_BLUE,
    ATK_GREEN,
    ATK_RED,
    ATK_YELLOW,
    CODE_COMMENT,
    CODE_FG,
    CODE_KEYWORD,
    CODE_STRING,
    DIALOG_BG,
    DIALOG_H,
    HEADER_BG,
    HEADER_H,
    HP_RED,
    INK,
    PANEL_BG,
    PANEL_FIELD,
    PANEL_GAP,
    PANEL_PAD,
    SCREEN_H,
    SCREEN_W,
    UI_BORDER,
)

ATTACKS = [
    ("Q-PREDICT", "TYPE/ NEURAL", ATK_RED, Match.do_q_predict),
    ("ENV.STEP()", "TYPE/ SYSTEM", ATK_BLUE, Match.do_env_step),
    ("TRAIN(100)", "TYPE/ LOOP", ATK_GREEN, Match.do_train),
    ("EPSILON++", "TYPE/ EXPLOIT", ATK_YELLOW, Match.do_epsilon),
]


def _attack_rects():
    area = pygame.Rect(
        PANEL_PAD,
        HEADER_H + 8,
        SCREEN_W - PANEL_PAD * 2,
        SCREEN_H - HEADER_H - DIALOG_H - 16,
    )
    bw = (area.w - PANEL_GAP) // 2
    bh = (area.h - PANEL_GAP) // 2
    return [
        pygame.Rect(area.x, area.y, bw, bh),
        pygame.Rect(area.x + bw + PANEL_GAP, area.y, bw, bh),
        pygame.Rect(area.x, area.y + bh + PANEL_GAP, bw, bh),
        pygame.Rect(area.x + bw + PANEL_GAP, area.y + bh + PANEL_GAP, bw, bh),
    ]


ATTACK_RECTS = _attack_rects()


def _header(surf, match):
    pygame.draw.rect(surf, HEADER_BG, pygame.Rect(0, 0, SCREEN_W, HEADER_H))
    pygame.draw.line(surf, UI_BORDER, (0, HEADER_H), (SCREEN_W, HEADER_H), 3)
    r = draw_text(surf, "import", font(SM), CODE_KEYWORD, (10, 6))
    draw_text(surf, " battleships", font(SM), CODE_FG, (r.right, 6))
    r = draw_text(surf, "game.start(", font(SM), CODE_FG, (10, 20))
    r = draw_text(surf, "'Battleship-v0'", font(SM), CODE_STRING, (r.right, 20))
    draw_text(surf, ")", font(SM), CODE_FG, (r.right, 20))
    heat_txt = "heat on" if match.show_heat else "heat off"
    draw_text(
        surf,
        f"eps {match.epsilon:.2f}  epoch {match.epoch}  {heat_txt}",
        font(SM),
        CODE_COMMENT,
        (10, 36),
    )


def _buttons(surf, match, pressed):
    pygame.draw.rect(surf, PANEL_FIELD, pygame.Rect(0, HEADER_H, SCREEN_W, SCREEN_H - 116))
    for i, rect in enumerate(ATTACK_RECTS):
        name, typ, color, _ = ATTACKS[i]
        if i == 0 and match.show_heat:
            typ = "TYPE/ HEAT ON"
        r = rect.move(2, 2) if pressed == i else rect
        pygame.draw.rect(surf, color, r, border_radius=8)
        pygame.draw.rect(surf, UI_BORDER, r, 3, border_radius=8)
        fg = INK if i == 3 else (255, 255, 255)
        edge = (80, 80, 80) if i == 3 else (40, 20, 20)
        name_h = draw_text_in(surf, name, font(MD), fg, r, r.y + 8, outline=edge, pad=8)
        draw_text_in(surf, typ, font(SM), fg, r, r.y + 10 + name_h, outline=edge, pad=8)
        shine = pygame.Surface((28, r.h), pygame.SRCALPHA)
        pygame.draw.polygon(shine, (255, 255, 255, 40), [(14, 0), (28, 0), (14, r.h), (0, r.h)])
        surf.blit(shine, (r.right - 28, r.y))


def _dialog(surf, match):
    box = pygame.Rect(0, SCREEN_H - DIALOG_H, SCREEN_W, DIALOG_H)
    pygame.draw.rect(surf, DIALOG_BG, box)
    pygame.draw.line(surf, (102, 102, 102), (0, box.y), (SCREEN_W, box.y), 4)
    lines = []
    for raw in match.dialog:
        lines.extend(wrap_text(raw, font(SM), SCREEN_W - 28))
    y = box.y + 8
    for line in lines[:3]:
        draw_text(surf, line, font(SM), INK, (10, y))
        y += 14
    bounce = 2 if (pygame.time.get_ticks() // 400) % 2 else 0
    ax, ay = SCREEN_W - 18, box.bottom - 14 + bounce
    pygame.draw.polygon(surf, HP_RED, [(ax, ay), (ax + 10, ay), (ax + 5, ay + 7)])


def render(surf, match, pressed=None):
    surf.fill(PANEL_BG)
    _header(surf, match)
    _buttons(surf, match, pressed)
    _dialog(surf, match)

    if match.paused:
        overlay.banner(surf, "PAUSE", alpha=120)
    if match.over:
        overlay.game_over(surf, match.winner())
