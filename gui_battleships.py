import os
from pathlib import Path

import pygame

import agent
from engine import Game

ROOT = Path(__file__).resolve().parent
FONT_PATH = ROOT / "assets" / "PressStart2P-Regular.ttf"

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

HEAT_RAMP = [
    (16, 20, 56),
    (56, 40, 128),
    (128, 48, 144),
    (200, 88, 112),
    (240, 152, 72),
    (255, 232, 160),
]

HEAT_LIFT = 3

BG = (43, 62, 80)
BG_STRIPE = (48, 70, 90)

SCREEN_W, SCREEN_H = 320, 240
TILE_W, TILE_H = 16, 8
COLS = "ABCDEFGHIJ"

BEZEL_PAD_UNIT = 7
SCREEN_GAP_UNIT = 8
UNIT_W = SCREEN_W + BEZEL_PAD_UNIT * 2
UNIT_H = SCREEN_H * 2 + SCREEN_GAP_UNIT + BEZEL_PAD_UNIT * 2
MIN_SCALE = 1.0
MAX_SCALE = 4.0
MARGIN_W = 0.95
MARGIN_H = 0.92

pygame.init()
pygame.display.set_caption("Battleship")


def desktop_size():
    try:
        return pygame.display.get_desktop_sizes()[0]
    except Exception:
        info = pygame.display.Info()
        return info.current_w, info.current_h


def fit_scale():
    override = os.environ.get("BATTLESHIP_SCALE")
    if override:
        try:
            value = float(override)
            if value > 0:
                return value
        except ValueError:
            pass
    dw, dh = desktop_size()
    by_w = dw * MARGIN_W / UNIT_W
    by_h = dh * MARGIN_H / UNIT_H
    return max(MIN_SCALE, min(by_w, by_h, MAX_SCALE))


def load_font(size):
    if FONT_PATH.exists():
        return pygame.font.Font(str(FONT_PATH), size)
    return pygame.font.SysFont("Consolas", size, bold=True)


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


def heat_color(t):
    t = max(0.0, min(1.0, t))
    seg = t * (len(HEAT_RAMP) - 1)
    i = min(int(seg), len(HEAT_RAMP) - 2)
    return lerp(HEAT_RAMP[i], HEAT_RAMP[i + 1], seg - i)


FLEET = [5, 4, 3, 3, 2]

HIT_WEIGHT = 12


def density_map(search):
    score = [0.0] * 100
    for size in FLEET:
        for row in range(10):
            for col in range(10):
                for dr, dc in ((0, 1), (1, 0)):
                    cells = []
                    for k in range(size):
                        r, c = row + dr * k, col + dc * k
                        if r > 9 or c > 9:
                            cells = []
                            break
                        idx = r * 10 + c
                        if search[idx] in ("M", "S"):
                            cells = []
                            break
                        cells.append(idx)
                    if not cells:
                        continue
                    weight = HIT_WEIGHT if any(search[i] == "H" for i in cells) else 1.0
                    for i in cells:
                        if search[i] == "U":
                            score[i] += weight
    return score


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


class BattleshipUi:
    def __init__(self):
        self.clock = pygame.time.Clock()
        self.top_surf = pygame.Surface((SCREEN_W, SCREEN_H))
        self.bot_surf = pygame.Surface((SCREEN_W, SCREEN_H))

        self.SCALE = fit_scale()
        sw = round(SCREEN_W * self.SCALE)
        sh = round(SCREEN_H * self.SCALE)
        pad = round(BEZEL_PAD_UNIT * self.SCALE)
        gap = round(SCREEN_GAP_UNIT * self.SCALE)
        self.win_w = sw + pad * 2
        self.win_h = sh * 2 + gap + pad * 2
        self.screen = pygame.display.set_mode((self.win_w, self.win_h))

        self.top_screen_rect = pygame.Rect(pad, pad, sw, sh)
        self.bot_screen_rect = pygame.Rect(pad, pad + sh + gap, sw, sh)
        self.top_bezel = self.top_screen_rect.inflate(pad, pad)
        self.bot_bezel = self.bot_screen_rect.inflate(pad, pad)

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
        self.show_heat = False
        self._heat_key = None
        self._heat = None
        self.paused = False
        self.auto_left = 0
        self.ai_delay = 0
        self.shot_anim_idx = None
        self.shot_anim_until = 0
        self.epsilon = 0.05
        self.epoch = 8402
        self.dialog = [
            "Gra rozpoczeta!",
            "Wybierz atak na dolnym ekranie.",
        ]
        self.running = True

    def screen_local(self, pos, rect):
        x = (pos[0] - rect.x) * SCREEN_W / rect.w
        y = (pos[1] - rect.y) * SCREEN_H / rect.h
        return x, y

    def current_search(self):
        return self.game.player1.search if self.game.player1_turn else self.game.player2.search

    def heat_values(self):
        search = self.game.player1.search
        key = "".join(search)
        if self._heat_key != key:
            raw = density_map(search)
            top = max(raw)
            self._heat = [v / top for v in raw] if top else [0.0] * 100
            self._heat_key = key
        return self._heat

    def cell_lift(self, idx, kind, enemy):
        if enemy and self.show_heat and kind == "water":
            return int(round(self.heat_values()[idx] * HEAT_LIFT))
        return {"water": 0, "ship": 2, "hit": 4, "miss": 1}[kind]

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
        if self.game.over or self.paused or self.auto_left > 0 or self.ai_delay > 0:
            return
        if not self.game.player1_turn:
            self.dialog = ["Poczekaj na swoja ture."]
            return
        if self.game.player1.search[index] != "U":
            self.dialog = [f"{coord_label(index)} juz ostrzelane.", "Wybierz inne pole."]
            return

        self.game.move(index)
        self.shot_anim_idx = index
        self.shot_anim_until = pygame.time.get_ticks() + 550
        result = self.game.player1.search[index]
        self._announce("GRACZ", move_name, index, result)
        self.predicted = None
        if self.game.over:
            return
        if not self.game.player1_turn:
            self.ai_delay = 700

    def _announce(self, who, move_name, index, result):
        line1 = f"{who} uzywa {move_name}!"
        if result == "M":
            line2 = f"Pudlo w {coord_label(index)}..."
        elif result == "S":
            line2 = f"Trafienie! Statek zatopiony {coord_label(index)}!"
        else:
            line2 = f"Trafienie w {coord_label(index)}!"
        self.dialog = [line1, line2]
        if self.game.over:
            winner = "GRACZ" if self.game.result == 1 else "AI"
            self.dialog.append(f"{winner} wygrywa!")

    def do_q_predict(self):
        self.show_heat = not self.show_heat
        if not self.show_heat:
            self.predicted = None
            self.dialog = ["Heatmapa wylaczona."]
            return
        if self.game.over or not self.game.player1_turn:
            self.dialog = ["Heatmapa wlaczona."]
            return
        idx = agent.pick_move(self.game.player1.search)
        if idx is None:
            self.dialog = ["Heatmapa wlaczona."]
            return
        self.predicted = idx
        self.cursor = idx
        self.dialog = [
            "GRACZ uzywa Q-PREDICT!",
            f"Heatmapa on. Agent wskazuje {coord_label(idx)}.",
        ]

    def do_env_step(self):
        self.fire(self.cursor, "ENV.STEP()")

    def do_train(self):
        if self.game.over:
            return
        self.auto_left = 100
        self.epoch += 100
        self.dialog = ["TRAIN(100) — petla uczenia", "Agent rozgrywa 100 krokow..."]

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
                who = "GRACZ" if self.game.player1_turn else "AI"
                self.game.move(idx)
                result = (self.game.player1.search if who == "GRACZ" else self.game.player2.search)[idx]
                self._announce(who, "TRAIN", idx, result)
                self.auto_left -= 1
            if self.auto_left <= 0 and not self.game.over:
                self.dialog = ["Trening zakonczony.", "Twoja tura, GRACZ."]
                if not self.game.player1_turn:
                    self.ai_delay = 400
            return

        if self.game.computer_turn and not self.game.player1_turn:
            self.ai_delay -= dt
            if self.ai_delay <= 0:
                self.ai_delay = 0
                idx = agent.pick_move(self.game.player2.search)
                if idx is None:
                    return
                self.game.move(idx)
                result = self.game.player2.search[idx]
                self._announce("AI", "Q-PREDICT", idx, result)
                if not self.game.over and not self.game.player1_turn:
                    self.ai_delay = 420
                else:
                    self.ai_delay = 0

    def move_cursor(self, dc, dr):
        row, col = self.cursor // 10, self.cursor % 10
        col = max(0, min(9, col + dc))
        row = max(0, min(9, row + dr))
        self.cursor = row * 10 + col

    def hit_iso(self, local, origin):
        lx, ly = local
        for i in range(100):
            kind = self.cell_enemy(i)
            lift = self.cell_lift(i, kind, True)
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
        elif key in (pygame.K_x, pygame.K_i, pygame.K_h):
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
        self._hud(surf, 8, 8, "AI", 99, ai_left / ai_total)
        self._hud(surf, SCREEN_W - 158, SCREEN_H - 50, "GRACZ", 12, pl_left / pl_total)

        shine = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        pygame.draw.polygon(shine, (255, 255, 255, 18), [(0, 0), (280, 0), (200, 90), (0, 70)])
        surf.blit(shine, (0, 0))

        if self.game.over:
            overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 130))
            surf.blit(overlay, (0, 0))
            winner = "GRACZ" if self.game.result == 1 else "AI"
            msg = FONT_LG.render(f"{winner} WINS!", False, (255, 255, 255))
            surf.blit(msg, msg.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2 - 10)))
            hint = FONT_MD.render("Press R to restart", False, (255, 255, 255))
            surf.blit(hint, hint.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2 + 18)))

    def _platform(self, surf, origin):
        cx, cy = origin[0], origin[1] + 36
        ellipse = pygame.Rect(0, 0, 168, 52)
        ellipse.center = (int(cx), int(cy))
        shadow = pygame.Surface(ellipse.size, pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (0, 0, 0, 70), shadow.get_rect())
        surf.blit(shadow, ellipse.topleft)

    def _board(self, surf, origin, enemy):
        bump_active = (
            enemy
            and self.shot_anim_idx is not None
            and pygame.time.get_ticks() < self.shot_anim_until
        )
        order = sorted(range(100), key=lambda i: (i // 10 + i % 10, i // 10))
        for i in order:
            col, row = i % 10, i // 10
            cx, cy = iso_center(col, row, origin)
            kind = self.cell_enemy(i) if enemy else self.cell_own(i)
            checker = (row + col) % 2 == 0
            bump_cell = bump_active and i == self.shot_anim_idx
            extra_lift = 2 if bump_cell else 0
            lift_now = self.cell_lift(i, kind, enemy)
            if kind == "water":
                if enemy and self.show_heat:
                    fill = heat_color(self.heat_values()[i])
                    draw_iso_cell(surf, cx, cy, fill, darken(fill), lift=lift_now + extra_lift)
                else:
                    fill = CELL_WATER if checker else lerp(CELL_WATER, (90, 170, 230), 0.25)
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
                    ring_col = (255, 70, 70)
                elif kind == "miss":
                    ring_col = (210, 210, 210)
                else:
                    ring_col = CELL_CURSOR
                pygame.draw.polygon(surf, ring_col, diamond(cx, cy - ring_lift), 3)

            if enemy and i == self.predicted and not bump_cell:
                pygame.draw.polygon(surf, CELL_PREDICT, diamond(cx, cy - lift_now), 2)
            if enemy and i == self.cursor and not bump_cell:
                pygame.draw.polygon(surf, CELL_CURSOR, diamond(cx, cy - lift_now), 2)

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
        draw_text(surf, " battleships", FONT_SM, (248, 248, 248), (r.right, 6))
        r = draw_text(surf, "game.start(", FONT_SM, (248, 248, 248), (10, 20))
        r = draw_text(surf, "'Battleship-v0'", FONT_SM, st, (r.right, 20))
        draw_text(surf, ")", FONT_SM, (248, 248, 248), (r.right, 20))
        heat_txt = "heat on" if self.show_heat else "heat off"
        draw_text(
            surf,
            f"eps {self.epsilon:.2f}  epoch {self.epoch}  {heat_txt}",
            FONT_SM,
            cm,
            (10, 36),
        )

        pygame.draw.rect(surf, (208, 216, 224), pygame.Rect(0, 54, SCREEN_W, SCREEN_H - 116))
        for i, rect in enumerate(self.atk_rects):
            name, typ, color, _ = self.atk_defs[i]
            if i == 0 and self.show_heat:
                typ = "TYPE/ HEAT ON"
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

        if self.game.over:
            overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 130))
            surf.blit(overlay, (0, 0))
            winner = "GRACZ" if self.game.result == 1 else "AI"
            msg = FONT_LG.render(f"{winner} WINS!", False, (255, 255, 255))
            surf.blit(msg, msg.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2 - 10)))
            hint = FONT_MD.render("Press R to restart", False, (255, 255, 255))
            surf.blit(hint, hint.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2 + 18)))

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
    BattleshipUi().run()
