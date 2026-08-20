import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import math
import numpy as np
import torch

from engine import Game

# Kanaly stanu
STATE_MAP = {"U": 0, "M": 1, "H": 2, "S": 3}
NUM_CHANNELS = len(STATE_MAP)

# Nagrody
# Skala blisko 1
REWARD_WIN = 10.0
REWARD_SUNK = 3.0
REWARD_HIT = 1.0
REWARD_MISS = -0.3


class BattleshipEnv:
    def __init__(self, max_steps=None):
        self.total_shots = 0
        self.game = Game(human1=False, human2=False)

        # Rozmiar planszy z engine
        self.cells = len(self.get_search())
        self.board_size = math.isqrt(self.cells)

        # Limit krokow
        self.max_steps = self.cells if max_steps is None else max_steps

        self.reset()

    # Agent search
    def get_search(self):
        return self.game.player1.search

    def get_state(self):
        search = self.get_search()

        # Kodowanie U/M/H/S na kanaly
        codes = np.fromiter((STATE_MAP[s] for s in search), dtype=np.int64, count=self.cells)

        # One-hot na kazde pole
        flat = np.zeros((NUM_CHANNELS, self.cells), dtype=np.float32)
        flat[codes, np.arange(self.cells)] = 1.0

        return torch.from_numpy(flat.reshape(NUM_CHANNELS, self.board_size, self.board_size))

    def get_valid_actions(self):
        search = self.get_search()

        # Tylko nieznane pola ("U")
        mask = np.fromiter(
            (1.0 if s == "U" else 0.0 for s in search), dtype=np.float32, count=len(search)
        )
        return torch.from_numpy(mask)

    def reset(self):
        # Nowa gra vs komputer
        self.game = Game(human1=False, human2=False)
        self.game.player1_turn = True
        self.total_shots = 0
        return self.get_state(), {"action_mask": self.get_valid_actions()}

    def step(self, action):
        search = self.get_search()

        # Pole juz ostrzelane
        if search[action] != "U":
            raise ValueError(f"Pole {action} jest juz ostrzelane. Maska akcji nie zadzialala.")

        # Stan przed strzalem
        old_hits = sum(1 for s in search if s in ("H", "S"))
        old_sunk = sum(1 for s in search if s == "S")

        # Strzal gracza 1
        self.game.player1_turn = True
        self.game.move(action)
        self.game.player1_turn = True
        self.total_shots += 1

        # Stan po strzale
        new_search = self.get_search()
        new_hits = sum(1 for s in new_search if s in ("H", "S"))
        new_sunk = sum(1 for s in new_search if s == "S")

        # Koniec gry
        terminated = self.game.over

        # Limit krokow
        truncated = not terminated and self.total_shots >= self.max_steps

        # Nagroda
        # Win > zatopiony > trafienie > pudlo
        if terminated:
            reward, event = REWARD_WIN, "win"
        elif new_sunk > old_sunk:
            reward, event = REWARD_SUNK, "sunk"
        elif new_hits > old_hits:
            reward, event = REWARD_HIT, "hit"
        else:
            reward, event = REWARD_MISS, "miss"

        info = {
            "event": event,
            "total_shots": self.total_shots,
            "action_mask": self.get_valid_actions(),
        }
        return self.get_state(), reward, terminated, truncated, info
