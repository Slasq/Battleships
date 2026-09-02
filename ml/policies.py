import os
import random

import heuristics
from ml.probmap.prior import load_bias
from ml.probmap.solver import best_move

ROOT = os.path.join(os.path.dirname(__file__), "..")
DQN_WEIGHTS = os.path.normpath(os.path.join(ROOT, "models", "dqn_main.pth"))

# Nazwy w gui
RANDOM = "random"
BASIC = "basic_ai"
PROBMAP = "probmap"
PROBMAP_PRIOR = "probmap_prior"
DQN = "dqn"

# Rozstrzyganie remisow
_rng = random.Random()

_bias = None
_dqn = None


def _get_bias():
    global _bias
    if _bias is None:
        _bias = load_bias()
    return _bias


# Wywolanie torcha
def _get_dqn():
    global _dqn
    if _dqn is None:
        from ml.dqn.agent import DQNAgent

        agent = DQNAgent(epsilon=0.0)
        agent.load(DQN_WEIGHTS)
        agent.policy_net.eval()
        _dqn = agent
    return _dqn


def _random(search):
    return heuristics.pick_random(search)


def _basic(search):
    return heuristics.pick_move(search)


def _probmap(search):
    return best_move(search, rng=_rng)


def _probmap_prior(search):
    return best_move(search, rng=_rng, bias=_get_bias())


def _dqn_move(search):
    import numpy as np
    import torch

    from ml.environment import NUM_CHANNELS, STATE_MAP

    cells = len(search)
    board = int(round(cells ** 0.5))

    # kod z BattleshipEnv.get_state
    codes = np.fromiter((STATE_MAP[s] for s in search), dtype=np.int64, count=cells)
    flat = np.zeros((NUM_CHANNELS, cells), dtype=np.float32)
    flat[codes, np.arange(cells)] = 1.0
    state = torch.from_numpy(flat.reshape(NUM_CHANNELS, board, board))

    mask = torch.tensor([1.0 if s == "U" else 0.0 for s in search])
    if mask.sum() == 0:
        return None

    return _get_dqn().select_action(state, mask)


POLICIES = {
    RANDOM: _random,
    BASIC: _basic,
    PROBMAP: _probmap,
    PROBMAP_PRIOR: _probmap_prior,
    DQN: _dqn_move,
}

LABELS = {
    RANDOM: "losowy",
    BASIC: "heurystyka",
    PROBMAP: "mapa gestosci",
    PROBMAP_PRIOR: "mapa gestosci z priorem",
    DQN: "siec DQN",
}


# Sprawdzenie czy wagi są wczytane poprawnie
def available(name):
    if name == DQN:
        return os.path.exists(DQN_WEIGHTS)
    return name in POLICIES

def get(name, fallback=PROBMAP):
    if name in POLICIES and available(name):
        return POLICIES[name]
    return POLICIES[fallback]


# Roztawianie kazda zwraca liste statkow jako krotki pól
UNIFORM = "uniform"
HUMAN = "human"


# Roztawienie z engine
def place_uniform(rng=None):
    from engine import player

    return [tuple(ship.indexes) for ship in player(rng=rng).ships]


# Rozstawienie wzorowane ruchami czlowieka
def place_human(rng=None):
    from ml.probmap.prior import sample_board

    return [tuple(cells) for cells in sample_board(_get_bias(), rng=rng)]


PLACERS = {
    UNIFORM: place_uniform,
    HUMAN: place_human,
}

PLACER_LABELS = {
    UNIFORM: "jednostajne",
    HUMAN: "jak czlowiek",
}


def placer(name, fallback=UNIFORM):
    return PLACERS.get(name, PLACERS[fallback])
