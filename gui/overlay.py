import pygame

from .fonts import LG, MD, font
from .theme import PAPER, SCREEN_H, SCREEN_W


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


def game_over(surf, winner):
    banner(surf, f"{winner} WINS!", "Press R to restart")
