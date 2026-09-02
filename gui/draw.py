import pygame

from .fonts import SM, font
from .theme import TILE_H, TILE_W


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def darken(color, amount=0.65):
    return tuple(max(0, int(c * amount)) for c in color)


def draw_text(surf, text, glyph_font, color, pos, outline=None):
    x, y = pos
    glyph = glyph_font.render(text, False, color)
    if outline is not None:
        shadow = glyph_font.render(text, False, outline)
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            surf.blit(shadow, (x + dx, y + dy))
    surf.blit(glyph, (x, y))
    return glyph.get_rect(topleft=(x, y))


def draw_text_in(surf, text, glyph_font, color, box, y, outline=None, pad=6):
    max_w = max(8, box.w - pad * 2)
    glyph = glyph_font.render(text, False, color)
    shadow = glyph_font.render(text, False, outline) if outline is not None else None
    if glyph.get_width() > max_w:
        h = max(1, round(glyph.get_height() * max_w / glyph.get_width()))
        glyph = pygame.transform.scale(glyph, (max_w, h))
        if shadow is not None:
            shadow = pygame.transform.scale(shadow, (max_w, h))
    x = box.x + pad
    if shadow is not None:
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            surf.blit(shadow, (x + dx, y + dy))
    surf.blit(glyph, (x, y))
    return glyph.get_height()


def tracked_text(text, glyph_font, color, tracking=0):
    glyphs = [glyph_font.render(ch, False, color) for ch in text]
    width = sum(g.get_width() for g in glyphs) + tracking * max(0, len(glyphs) - 1)
    height = glyph_font.get_height()
    surf = pygame.Surface((max(1, width), height), pygame.SRCALPHA)
    x = 0
    for glyph in glyphs:
        surf.blit(glyph, (x, 0))
        x += glyph.get_width() + tracking
    return surf


def wrap_text(text, glyph_font, max_width):
    words = text.split()
    if not words:
        return [""]
    lines, current = [], words[0]
    for word in words[1:]:
        trial = f"{current} {word}"
        if glyph_font.size(trial)[0] <= max_width:
            current = trial
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def diamond(cx, cy, tw=TILE_W, th=TILE_H):
    return [
        (cx, cy - th / 2),
        (cx + tw / 2, cy),
        (cx, cy + th / 2),
        (cx - tw / 2, cy),
    ]


def iso_center(col, row, origin):
    ox, oy = origin
    return ox + (col - row) * (TILE_W / 2), oy + (col + row) * (TILE_H / 2)


def point_in_diamond(px, py, cx, cy):
    dx = abs(px - cx) / (TILE_W / 2)
    dy = abs(py - cy) / (TILE_H / 2)
    return dx + dy <= 1.05


def draw_iso_cell(surf, cx, cy, fill, side, lift=0, mark=None, outline=None):
    h = lift
    top_y = cy - h
    if h > 0:
        pygame.draw.polygon(
            surf,
            darken(side, 0.75),
            [
                (cx - TILE_W / 2, cy),
                (cx, cy + TILE_H / 2),
                (cx, cy + TILE_H / 2 - h),
                (cx - TILE_W / 2, cy - h),
            ],
        )
        pygame.draw.polygon(
            surf,
            side,
            [
                (cx + TILE_W / 2, cy),
                (cx, cy + TILE_H / 2),
                (cx, cy + TILE_H / 2 - h),
                (cx + TILE_W / 2, cy - h),
            ],
        )
    pygame.draw.polygon(surf, fill, diamond(cx, top_y))
    pygame.draw.polygon(surf, darken(fill, 0.72), diamond(cx, top_y), 1)
    if outline:
        pygame.draw.polygon(surf, outline, diamond(cx, top_y), 2)
    if mark:
        glyph = font(SM).render(mark, False, (255, 255, 255) if mark == "X" else (68, 68, 68))
        glyph = pygame.transform.rotate(glyph, 45)
        rect = glyph.get_rect(center=(cx, top_y - 1))
        surf.blit(glyph, rect)
