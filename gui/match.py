import pygame

import agent
from engine import Game

from .heatmap import HEAT_LIFT, normalized_density
from .theme import COLS

LIFT = {"water": 0, "ship": 2, "hit": 4, "miss": 1}

SHOT_ANIM_MS = 550
AI_DELAY_MS = 700
AI_CHAIN_MS = 420
TRAIN_STEPS = 100
TRAIN_PER_FRAME = 2


def coord_label(index):
    row, col = index // 10, index % 10
    return f"[{COLS[col]}, {row + 1}]"


def remaining_hp(ship_indexes, attacker_search):
    total = max(1, len(ship_indexes))
    left = sum(1 for i in ship_indexes if attacker_search[i] == "U")
    return left, total


class Match:
    def __init__(self):
        self.reset()

    def reset(self):
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

    @property
    def over(self):
        return self.game.over

    def current_search(self):
        return self.game.player1.search if self.game.player1_turn else self.game.player2.search

    def heat_values(self):
        search = self.game.player1.search
        key = "".join(search)
        if self._heat_key != key:
            self._heat = normalized_density(search)
            self._heat_key = key
        return self._heat

    def cell_lift(self, idx, kind, enemy):
        if enemy and self.show_heat and kind == "water":
            return int(round(self.heat_values()[idx] * HEAT_LIFT))
        return LIFT[kind]

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

    def shot_bump(self, idx):
        return (
            self.shot_anim_idx is not None
            and idx == self.shot_anim_idx
            and pygame.time.get_ticks() < self.shot_anim_until
        )

    def move_cursor(self, dc, dr):
        row, col = self.cursor // 10, self.cursor % 10
        col = max(0, min(9, col + dc))
        row = max(0, min(9, row + dr))
        self.cursor = row * 10 + col

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
        self.shot_anim_until = pygame.time.get_ticks() + SHOT_ANIM_MS
        result = self.game.player1.search[index]
        self._announce("GRACZ", move_name, index, result)
        self.predicted = None
        if self.game.over:
            return
        if not self.game.player1_turn:
            self.ai_delay = AI_DELAY_MS

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
            winner = self.winner()
            self.dialog.append(f"{winner} wygrywa!")

    def winner(self):
        return "GRACZ" if self.game.result == 1 else "AI"

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
        self.auto_left = TRAIN_STEPS
        self.epoch += TRAIN_STEPS
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

    def tick(self, dt):
        if self.paused or self.game.over:
            return
        if self.auto_left > 0:
            self._tick_train()
            return
        self._tick_ai(dt)

    def _tick_train(self):
        for _ in range(TRAIN_PER_FRAME):
            if self.auto_left <= 0 or self.game.over:
                break
            idx = agent.pick_move(self.current_search())
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

    def _tick_ai(self, dt):
        if not (self.game.computer_turn and not self.game.player1_turn):
            return
        self.ai_delay -= dt
        if self.ai_delay > 0:
            return
        self.ai_delay = 0
        idx = agent.pick_move(self.game.player2.search)
        if idx is None:
            return
        self.game.move(idx)
        self._announce("AI", "Q-PREDICT", idx, self.game.player2.search[idx])
        if not self.game.over and not self.game.player1_turn:
            self.ai_delay = AI_CHAIN_MS
        else:
            self.ai_delay = 0
