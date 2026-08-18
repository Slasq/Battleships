"""Eksperymentalny UI Pokemon RL — pygame, nie HTML."""

from pathlib import Path

import pygame

import agent
from engine import Game

ROOT = Path(__file__).resolve().parent
FONT_PATH = ROOT / "assets" / "PressStart2P-Regular.ttf"

# --- paleta z mockupu ---
BEZEL = (17, 17, 17)
BEZEL_EDGE = (48, 56, 68)

SKY_TOP = (152, 200, 248)
SKY_BOTTOM = (248, 252, 248)
WATER = (40, 120, 200)
WATER_DEEP = (26, 90, 154)

DIALOG_BG = (252, 252, 252)
HP_GREEN = (72, 208, 72)
HP_YELLOW = (248, 208, 48)
HP_RED = (248, 88, 56)
UI_BORDER = (64, 64, 64)
HUD_BG = (255, 255, 232)

ATK_RED = (248, 88, 56)
ATK_BLUE = (56, 136, 216)
ATK_GREEN = (72, 208, 72)
ATK_YELLOW = (248, 208, 48)

CELL_WATER = (56, 136, 216)
CELL_SHIP = (120, 200, 80)
CELL_SHIP_SIDE = (74, 138, 42)
CELL_HIT = (248, 88, 56)
CELL_HIT_SIDE = (168, 32, 16)
CELL_MISS = (255, 255, 255)
CELL_MISS_SIDE = (204, 204, 204)
CELL_CURSOR = (255, 255, 160)
CELL_PREDICT = (255, 120, 220)

BG = (43, 62, 80)
BG_STRIPE = (48, 70, 90)

SCREEN_W, SCREEN_H = 320, 240
TILE_W, TILE_H = 16, 8
COLS = "ABCDEFGHIJ"

pygame.init()
pygame.display.set_caption("Battleship - Pokemon RL Edition")


def load_font(size):
    if FONT_PATH.exists():
        return pygame.font.Font(str(FONT_PATH), size)
    return pygame.font.SysFont("Consolas", size, bold=True)


# Press Start 2P: 8px miesci sie w przyciskach, 10px na HUD/dialog.
FONT_MARK = load_font(8)
FONT_SM = load_font(8)
FONT_MD = load_font(8)
FONT_LG = load_font(16)


def draw_text(surf, text, font, color, pos, outline=None):
    x, y = pos
    glyph = font.render(text, False, color)
    if outline is not None:
        shadow = font.render(text, False, outline)
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            surf.blit(shadow, (x + dx, y + dy))
    surf.blit(glyph, (x, y))
    return glyph.get_rect(topleft=(x, y))


def draw_text_in(surf, text, font, color, box, y, outline=None, pad=6):
    """Rysuje tekst w przycisku, skalujac w poziomie gdy nie miesci sie."""
    max_w = max(8, box.w - pad * 2)
    glyph = font.render(text, False, color)
    shadow = font.render(text, False, outline) if outline is not None else None
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


def wrap_text(text, font, max_width):
    words = text.split()
    if not words:
        return [""]
    lines, current = [], words[0]
    for word in words[1:]:
        trial = f"{current} {word}"
        if font.size(trial)[0] <= max_width:
            current = trial
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def darken(color, amount=0.65):
    return tuple(max(0, int(c * amount)) for c in color)


def coord_label(index):
    row, col = index // 10, index % 10
    return f"[{COLS[col]}, {row + 1}]"


def hp_color(ratio):
    if ratio > 0.5:
        return HP_GREEN
    if ratio > 0.2:
        return HP_YELLOW
    return HP_RED


def remaining_hp(ship_indexes, attacker_search):
    total = max(1, len(ship_indexes))
    left = sum(1 for i in ship_indexes if attacker_search[i] == "U")
    return left, total


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
        glyph = FONT_MARK.render(mark, False, (255, 255, 255) if mark == "X" else (68, 68, 68))
        glyph = pygame.transform.rotate(glyph, 45)
        rect = glyph.get_rect(center=(cx, top_y - 1))
        surf.blit(glyph, rect)


class NdsUi:
    SCALE = 2
    BEZEL_PAD = 14
    SCREEN_GAP = 16

    def __init__(self):
        self.clock = pygame.time.Clock()
        self.top_surf = pygame.Surface((SCREEN_W, SCREEN_H))
        self.bot_surf = pygame.Surface((SCREEN_W, SCREEN_H))

        sw = SCREEN_W * self.SCALE
        sh = SCREEN_H * self.SCALE
        pad = self.BEZEL_PAD
        gap = self.SCREEN_GAP
        self.win_w = sw + pad * 2
        self.win_h = sh * 2 + gap + pad * 2
        self.screen = pygame.display.set_mode((self.win_w, self.win_h))

        self.top_screen_rect = pygame.Rect(pad, pad, sw, sh)
        self.bot_screen_rect = pygame.Rect(pad, pad + sh + gap, sw, sh)
        self.top_bezel = self.top_screen_rect.inflate(pad, pad)
        self.bot_bezel = self.bot_screen_rect.inflate(pad, pad)

        # izometryczne origin (środek komórki 0,0)
        self.ai_origin = (228, 42)
        self.player_origin = (92, 128)

        self.reset_match()

        self.atk_defs = [
            ("Q-PREDICT", "TYPE/ NEURAL", ATK_RED, self.do_q_predict),
            ("ENV.STEP()", "TYPE/ SYSTEM", ATK_BLUE, self.do_env_step),
            ("TRAIN(100)", "TYPE/ LOOP", ATK_GREEN, self.do_train),
            ("EPSILON++", "TYPE/ EXPLOIT", ATK_YELLOW, self.do_epsilon),
        ]
        pad, gap = 10, 8
        header_h, dialog_h = 54, 62
        area = pygame.Rect(pad, header_h + 8, SCREEN_W - pad * 2, SCREEN_H - header_h - dialog_h - 16)
        bw = (area.w - gap) // 2
        bh = (area.h - gap) // 2
        self.atk_rects = [
            pygame.Rect(area.x, area.y, bw, bh),
            pygame.Rect(area.x + bw + gap, area.y, bw, bh),
            pygame.Rect(area.x, area.y + bh + gap, bw, bh),
            pygame.Rect(area.x + bw + gap, area.y + bh + gap, bw, bh),
        ]

        self.pressed_atk = None

    def reset_match(self):
        self.game = Game(True, False)
        self.cursor = 44
        self.predicted = None
        self.paused = False
        self.auto_left = 0
        self.ai_delay = 0
        self.epsilon = 0.05
        self.epoch = 8402
        self.dialog = [
            "Wild DQN_AGENT appeared!",
            "Wybierz atak na dolnym ekranie.",
        ]
        self.running = True

    def screen_local(self, pos, rect):
        x = (pos[0] - rect.x) / self.SCALE
        y = (pos[1] - rect.y) / self.SCALE
        return x, y

    def current_search(self):
        return self.game.player1.search if self.game.player1_turn else self.game.player2.search

    def cell_own(self, idx):
        shot = self.game.player2.search[idx]
        if shot in ("H", "S"):
            return "hit"
        if shot == "M":
            return "miss"
        if idx in self.game.player1.indexes:
            return "ship"
        return "water"

    def cell_enemy(self, idx):
        shot = self.game.player1.search[idx]
        if shot in ("H", "S"):
            return "hit"
        if shot == "M":
            return "miss"
        return "water"

    def fire(self, index, move_name):
        if self.game.over or self.paused or self.auto_left or self.ai_delay:
            return
        if not self.game.player1_turn:
            self.dialog = ["Poczekaj na turę ENV_WRAPPER."]
            return
        if self.game.player1.search[index] != "U":
            self.dialog = [f"{coord_label(index)} już ostrzelane.", "Wybierz inne pole."]
            return

        shooter = "ENV_WRAPPER"
        self.game.move(index)
        result = self.game.player1.search[index]
        self._announce(shooter, move_name, index, result)
        self.predicted = None
        if self.game.over:
            return
        if not self.game.player1_turn:
            self.ai_delay = 700

    def _announce(self, who, move_name, index, result):
        wild = "Dziki " if who == "DQN_AGENT" else ""
        line1 = f"{wild}{who} użył {move_name}!"
        if result == "M":
            line2 = f"Pudło w {coord_label(index)}..."
        elif result == "S":
            line2 = f"Trafienie krytyczne! Statek zatopiony {coord_label(index)}!"
        else:
            line2 = f"Trafienie krytyczne w {coord_label(index)}!"
        self.dialog = [line1, line2]
        if self.game.over:
            winner = "ENV_WRAPPER" if self.game.result == 1 else "DQN_AGENT"
            self.dialog.append(f"{winner} wygrywa walkę!")

    def do_q_predict(self):
        if self.game.over or not self.game.player1_turn:
            return
        idx = agent.pick_move(self.game.player1.search)
        if idx is None:
            return
        self.predicted = idx
        self.cursor = idx
        self.dialog = [
            "ENV_WRAPPER użył Q-PREDICT!",
            f"Sieć wskazuje {coord_label(idx)}.",
        ]

    def do_env_step(self):
        target = self.cursor
        self.fire(target, "ENV.STEP()")

    def do_train(self):
        if self.game.over:
            return
        self.auto_left = 100
        self.epoch += 100
        self.dialog = ["TRAIN(100) — pętla uczenia", "Agent rozgrywa 100 kroków..."]

    def do_epsilon(self):
        self.epsilon = min(1.0, self.epsilon + 0.05)
        if self.game.over or not self.game.player1_turn:
            return
        idx = agent.pick_random(self.game.player1.search)
        if idx is None:
            return
        self.cursor = idx
        self.fire(idx, "EPSILON++")

    def tick_ai(self, dt):
        if self.paused or self.game.over:
            return
        if self.auto_left > 0:
            steps = 2
            for _ in range(steps):
                if self.auto_left <= 0 or self.game.over:
                    break
                search = self.current_search()
                idx = agent.pick_move(search)
                if idx is None:
                    self.auto_left = 0
                    break
                who = "ENV_WRAPPER" if self.game.player1_turn else "DQN_AGENT"
                self.game.move(idx)
                result = (self.game.player1.search if who == "ENV_WRAPPER" else self.game.player2.search)[idx]
                self._announce(who, "TRAIN", idx, result)
                self.auto_left -= 1
            if self.auto_left <= 0 and not self.game.over:
                self.dialog = ["Trening zakończony.", "Twoja tura, ENV_WRAPPER."]
                if not self.game.player1_turn:
                    self.ai_delay = 400
            return

        if self.game.computer_turn and not self.game.player1_turn:
            self.ai_delay -= dt
            if self.ai_delay <= 0:
                idx = agent.pick_move(self.game.player2.search)
                if idx is None:
                    return
                self.game.move(idx)
                result = self.game.player2.search[idx]
                self._announce("DQN_AGENT", "Q-PREDICT", idx, result)
                if not self.game.over and not self.game.player1_turn:
                    self.ai_delay = 420

    def move_cursor(self, dc, dr):
        row, col = self.cursor // 10, self.cursor % 10
        col = max(0, min(9, col + dc))
        row = max(0, min(9, row + dr))
        self.cursor = row * 10 + col

    def hit_iso(self, local, origin):
        lx, ly = local
        for i in range(100):
            kind = self.cell_enemy(i)
            lift = {"water": 0, "ship": 2, "hit": 4, "miss": 1}[kind]
            cx, cy = iso_center(i % 10, i // 10, origin)
            if point_in_diamond(lx, ly, cx, cy - lift):
                return i
        return None

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            self.running = False
        elif event.type == pygame.KEYDOWN:
            self._key(event.key)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._click(event.pos)
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.pressed_atk = None

    def _key(self, key):
        if key == pygame.K_ESCAPE:
            self.running = False
        elif key == pygame.K_SPACE:
            self.paused = not self.paused
        elif key == pygame.K_r:
            self.reset_match()
        elif key == pygame.K_t:
            self.do_train()
        elif key == pygame.K_e:
            self.do_epsilon()
        elif key in (pygame.K_UP, pygame.K_w):
            self.move_cursor(0, -1)
        elif key in (pygame.K_DOWN, pygame.K_s):
            self.move_cursor(0, 1)
        elif key in (pygame.K_LEFT, pygame.K_a):
            self.move_cursor(-1, 0)
        elif key in (pygame.K_RIGHT, pygame.K_d):
            self.move_cursor(1, 0)
        elif key in (pygame.K_RETURN, pygame.K_k):
            self.do_env_step()
        elif key in (pygame.K_x, pygame.K_i):
            self.do_q_predict()
        elif key in (pygame.K_y, pygame.K_j):
            self.do_epsilon()
        elif key in (pygame.K_z, pygame.K_b):
            self.predicted = None

    def _click(self, pos):
        if self.top_screen_rect.collidepoint(pos):
            local = self.screen_local(pos, self.top_screen_rect)
            hit = self.hit_iso(local, self.ai_origin)
            if hit is not None:
                self.cursor = hit
                self.do_env_step()
                return
        if self.bot_screen_rect.collidepoint(pos):
            local = self.screen_local(pos, self.bot_screen_rect)
            for i, rect in enumerate(self.atk_rects):
                if rect.collidepoint(local):
                    self.pressed_atk = i
                    self.atk_defs[i][3]()
                    return

    def draw_background(self):
        self.screen.fill(BG)
        for i in range(-self.win_h, self.win_w, 16):
            pygame.draw.line(self.screen, BG_STRIPE, (i, 0), (i + self.win_h, self.win_h), 2)

    def draw_frames(self):
        for bezel in (self.top_bezel, self.bot_bezel):
            pygame.draw.rect(self.screen, BEZEL, bezel, border_radius=8)
            pygame.draw.rect(self.screen, BEZEL_EDGE, bezel, 2, border_radius=8)

    def draw_top_screen(self):
        surf = self.top_surf
        horizon = int(SCREEN_H * 0.45)
        for y in range(SCREEN_H):
            if y < horizon:
                color = lerp(SKY_TOP, SKY_BOTTOM, y / horizon)
            else:
                color = lerp(WATER, WATER_DEEP, (y - horizon) / (SCREEN_H - horizon))
            pygame.draw.line(surf, color, (0, y), (SCREEN_W, y))

        self._platform(surf, self.ai_origin)
        self._platform(surf, self.player_origin)
        self._board(surf, self.ai_origin, enemy=True)
        self._board(surf, self.player_origin, enemy=False)

        ai_left, ai_total = remaining_hp(self.game.player2.indexes, self.game.player1.search)
        pl_left, pl_total = remaining_hp(self.game.player1.indexes, self.game.player2.search)
        self._hud(surf, 8, 8, "DQN_AGENT", 99, ai_left / ai_total)
        self._hud(surf, SCREEN_W - 158, SCREEN_H - 50, "ENV_WRAPPER", 12, pl_left / pl_total)

        shine = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        pygame.draw.polygon(shine, (255, 255, 255, 18), [(0, 0), (280, 0), (200, 90), (0, 70)])
        surf.blit(shine, (0, 0))

    def _platform(self, surf, origin):
        cx, cy = origin[0], origin[1] + 36
        ellipse = pygame.Rect(0, 0, 168, 52)
        ellipse.center = (int(cx), int(cy))
        shadow = pygame.Surface(ellipse.size, pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (0, 0, 0, 70), shadow.get_rect())
        surf.blit(shadow, ellipse.topleft)

    def _board(self, surf, origin, enemy):
        lifts = {"water": 0, "ship": 2, "hit": 4, "miss": 1}
        order = sorted(range(100), key=lambda i: (i // 10 + i % 10, i // 10))
        for i in order:
            col, row = i % 10, i // 10
            cx, cy = iso_center(col, row, origin)
            kind = self.cell_enemy(i) if enemy else self.cell_own(i)
            checker = (row + col) % 2 == 0
            if kind == "water":
                fill = CELL_WATER if checker else lerp(CELL_WATER, (90, 170, 230), 0.25)
                draw_iso_cell(surf, cx, cy, fill, darken(CELL_WATER), lift=0)
            elif kind == "ship":
                draw_iso_cell(surf, cx, cy, CELL_SHIP, CELL_SHIP_SIDE, lift=2)
            elif kind == "hit":
                draw_iso_cell(surf, cx, cy, CELL_HIT, CELL_HIT_SIDE, lift=4, mark="X")
            elif kind == "miss":
                draw_iso_cell(surf, cx, cy, CELL_MISS, CELL_MISS_SIDE, lift=1, mark="o")

            if enemy and i == self.predicted:
                pygame.draw.polygon(surf, CELL_PREDICT, diamond(cx, cy - lifts[kind]), 2)
            if enemy and i == self.cursor:
                pygame.draw.polygon(surf, CELL_CURSOR, diamond(cx, cy - lifts[kind]), 2)

    def _hud(self, surf, x, y, name, lvl, ratio):
        box = pygame.Rect(x, y, 150, 42)
        pygame.draw.rect(surf, HUD_BG, box, border_radius=10)
        pygame.draw.rect(surf, UI_BORDER, box, 3, border_radius=10)
        draw_text(surf, name, FONT_MD, (17, 17, 17), (x + 8, y + 6))
        bar = pygame.Rect(x + 30, y + 26, 78, 8)
        pygame.draw.rect(surf, (72, 64, 64), bar.inflate(4, 4), border_radius=4)
        pygame.draw.rect(surf, (224, 224, 224), bar, border_radius=3)
        inner = bar.inflate(-4, -4)
        pygame.draw.rect(surf, (80, 104, 80), inner)
        fill_w = max(0, int(inner.w * max(0.0, min(1.0, ratio))))
        if fill_w:
            pygame.draw.rect(surf, hp_color(ratio), pygame.Rect(inner.x, inner.y, fill_w, inner.h))
        draw_text(surf, "HP", FONT_SM, (248, 176, 48), (x + 8, y + 24), outline=(80, 48, 0))
        lvl_s = FONT_SM.render(f"Lv{lvl}", False, (51, 51, 51))
        surf.blit(lvl_s, (x + 142 - lvl_s.get_width(), y + 24))

    def draw_bottom_screen(self):
        surf = self.bot_surf
        surf.fill((224, 232, 240))

        header = pygame.Rect(0, 0, SCREEN_W, 54)
        pygame.draw.rect(surf, (56, 56, 56), header)
        pygame.draw.line(surf, UI_BORDER, (0, 54), (SCREEN_W, 54), 3)
        kw, st, cm = (248, 168, 56), (168, 224, 120), (170, 170, 170)
        r = draw_text(surf, "import", FONT_SM, kw, (10, 6))
        draw_text(surf, " gym as gym", FONT_SM, (248, 248, 248), (r.right, 6))
        r = draw_text(surf, "gym.make(", FONT_SM, (248, 248, 248), (10, 20))
        r = draw_text(surf, "'Battleship-v0'", FONT_SM, st, (r.right, 20))
        draw_text(surf, ")", FONT_SM, (248, 248, 248), (r.right, 20))
        draw_text(surf, f"eps {self.epsilon:.2f}  epoch {self.epoch}", FONT_SM, cm, (10, 36))

        pygame.draw.rect(surf, (208, 216, 224), pygame.Rect(0, 54, SCREEN_W, SCREEN_H - 116))
        for i, rect in enumerate(self.atk_rects):
            name, typ, color, _ = self.atk_defs[i]
            r = rect.move(2, 2) if self.pressed_atk == i else rect
            pygame.draw.rect(surf, color, r, border_radius=8)
            pygame.draw.rect(surf, UI_BORDER, r, 3, border_radius=8)
            fg = (17, 17, 17) if i == 3 else (255, 255, 255)
            edge = (80, 80, 80) if i == 3 else (40, 20, 20)
            name_h = draw_text_in(surf, name, FONT_MD, fg, r, r.y + 8, outline=edge, pad=8)
            draw_text_in(surf, typ, FONT_SM, fg, r, r.y + 10 + name_h, outline=edge, pad=8)
            shine = pygame.Surface((28, r.h), pygame.SRCALPHA)
            pygame.draw.polygon(shine, (255, 255, 255, 40), [(14, 0), (28, 0), (14, r.h), (0, r.h)])
            surf.blit(shine, (r.right - 28, r.y))

        dialog = pygame.Rect(0, SCREEN_H - 62, SCREEN_W, 62)
        pygame.draw.rect(surf, DIALOG_BG, dialog)
        pygame.draw.line(surf, (102, 102, 102), (0, dialog.y), (SCREEN_W, dialog.y), 4)
        lines = []
        for raw in self.dialog:
            lines.extend(wrap_text(raw, FONT_SM, SCREEN_W - 28))
        y = dialog.y + 8
        for line in lines[:3]:
            draw_text(surf, line, FONT_SM, (17, 17, 17), (10, y))
            y += 14
        bounce = 2 if (pygame.time.get_ticks() // 400) % 2 else 0
        ax, ay = SCREEN_W - 18, dialog.bottom - 14 + bounce
        pygame.draw.polygon(surf, HP_RED, [(ax, ay), (ax + 10, ay), (ax + 5, ay + 7)])

        if self.paused:
            overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 120))
            surf.blit(overlay, (0, 0))
            msg = FONT_LG.render("PAUSE", False, (255, 255, 255))
            surf.blit(msg, msg.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2)))

    def blit_screens(self):
        top = pygame.transform.scale(self.top_surf, self.top_screen_rect.size)
        bot = pygame.transform.scale(self.bot_surf, self.bot_screen_rect.size)
        self.screen.blit(top, self.top_screen_rect)
        self.screen.blit(bot, self.bot_screen_rect)

    def run(self):
        while self.running:
            dt = self.clock.tick(60)
            for event in pygame.event.get():
                self.handle_event(event)
            if not self.paused:
                self.tick_ai(dt)
            self.draw_background()
            self.draw_frames()
            self.draw_top_screen()
            self.draw_bottom_screen()
            self.blit_screens()
            pygame.display.flip()
        pygame.quit()


if __name__ == "__main__":
    NdsUi().run()
