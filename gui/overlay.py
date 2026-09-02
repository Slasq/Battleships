import pygame

from .fonts import LG, MD, font
from .theme import HP_YELLOW, PAPER, SCREEN_H, SCREEN_W


def dim(surf, alpha):
    layer = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    layer.fill((0, 0, 0, alpha))
    surf.blit(layer, (0, 0))


def banner(surf, title, hint=None, alpha=130):
    dim(surf, alpha)
    msg = font(LG).render(title, False, PAPER)
    if hint is None:
        surf.blit(msg, msg.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2)))
        return
    surf.blit(msg, msg.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2 - 10)))
    tip = font(MD).render(hint, False, PAPER)
    surf.blit(tip, tip.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2 + 18)))


def hint(surf, key, label, y):
    parts = [
        (font(MD).render(key, False, HP_YELLOW)),
        (font(MD).render(" - ", False, PAPER)),
        (font(MD).render(label, False, PAPER)),
    ]
    x = (SCREEN_W - sum(p.get_width() for p in parts)) // 2
    for part in parts:
        surf.blit(part, (x, y))
        x += part.get_width()


def game_over(surf, winner):
    dim(surf, 130)
    msg = font(LG).render(f"{winner} WINS!", False, PAPER)
    surf.blit(msg, msg.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2 - 18)))
    hint(surf, "R", "JESZCZE RAZ", SCREEN_H // 2 + 6)
    hint(surf, "A", "ANALIZA", SCREEN_H // 2 + 22)
