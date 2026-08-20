import sys
import os
import numpy as np
import torch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from engine import Game

# Mapowanie stanu pola na kanal
STATE_MAP = {"U": 0, "M": 1, "H": 2, "S": 3}
NUM_CHANNELS = 4


class BattleshipEnv:
    def __init__(self):
        self.game = None
        self.total_shots = 0
        self.reset()

    def reset(self):
        # Nowa gra agent zawsze jako player1
        self.game = Game(human1=False, human2=False)
        self.game.player1_turn = True
        self.total_shots = 0
        return self.get_state()

    def get_search(self):
        return self.game.player1.search

    def get_state(self):
        # One-hot 4 kanaly x 10x10
        search = self.get_search()
        state = np.zeros((NUM_CHANNELS, 10, 10), dtype=np.float32)
        for idx, s in enumerate(search):
            ch = STATE_MAP[s]
            state[ch, idx // 10, idx % 10] = 1.0
        return torch.tensor(state)

    def get_valid_actions(self):
        # Maskowanie juz ostrzelanych pol
        search = self.get_search()
        return torch.tensor([1.0 if s == "U" else 0.0 for s in search])

    def step(self, action: int):
        search = self.get_search()

        # Nielegalny ruch
        if search[action] != "U":
            return self.get_state(), -5.0, False, {"event": "invalid"}

        # Stan przed strzalem
        old_hits = sum(1 for s in search if s in ("H", "S"))
        old_sunk = sum(1 for s in search if s == "S")

        # Strzal agentem (trzymamy ture player1)
        self.game.player1_turn = True
        self.game.move(action)
        self.game.player1_turn = True
        self.total_shots += 1

        # Stan po strzale
        new_search = self.get_search()
        new_hits = sum(1 for s in new_search if s in ("H", "S"))
        new_sunk = sum(1 for s in new_search if s == "S")

        done = self.game.over

        # Nagrody: win > zatopiony > hit > miss
        if done:
            reward = 10.0
        elif new_sunk > old_sunk:
            reward = 3.0
        elif new_hits > old_hits:
            reward = 1.0
        else:
            reward = -0.3

        info = {
            "event": "win" if done else "sunk" if new_sunk > old_sunk else "hit" if new_hits > old_hits else "miss",
            "total_shots": self.total_shots,
        }
        return self.get_state(), reward, done, info
