import math
import random

from ml.probmap.prior import uniform_occupancy
from ml.probmap.solver import BOARD_SIZE, DEFAULT_FLEET, placements, probability_map

BETA = 2.0

# Mkas prób roztawianie
MAX_TRIES = 100

SAMPLES = 5000

_hide = {}


# Przeszukiwanie pustej planszy przedzial 0-1 strzela w najwyszą wartośc
def hide_map(board_size=BOARD_SIZE):
    if board_size not in _hide:
        raw = probability_map(["U"] * (board_size * board_size))
        lo, hi = min(raw), max(raw)
        _hide[board_size] = [(v - lo) / (hi - lo) for v in raw]

    return _hide[board_size]


# Szukanie optymalnego ustawienia
def _try_place(rng, beta, fleet, board_size):
    hide = hide_map(board_size)
    taken = set()
    flota = []

    for size in fleet:
        opcje = []
        wagi = []

        for p in placements(size, board_size):
            if taken.intersection(p):
                continue

            gestosc = sum(hide[i] for i in p) / len(p)
            opcje.append(p)
            wagi.append(math.exp(-beta * gestosc))

        if not opcje:
            return None

        p = rng.choices(opcje, weights=wagi, k=1)[0]
        flota.append(tuple(p))
        taken.update(p)

    return flota


# Roztawienie z losowymi wagami im chlodniej na heatmapie tym chetniej tam postawi
def place(rng=None, beta=BETA, fleet=DEFAULT_FLEET, board_size=BOARD_SIZE, tries=MAX_TRIES):
    if rng is None:
        rng = random

    for _ in range(tries):
        flota = _try_place(rng, beta, fleet, board_size)
        if flota is not None:
            return flota

    raise RuntimeError(f"nie ulozono floty w {tries} probach, beta={beta}")


# Jak czesto rozstawienie zajmuje wszystkie ploa
def hide_occupancy(beta=BETA, samples=SAMPLES, rng=None, fleet=DEFAULT_FLEET,
                   board_size=BOARD_SIZE):
    if rng is None:
        rng = random

    counts = [0] * (board_size * board_size)

    for _ in range(samples):
        for p in place(rng, beta, fleet, board_size):
            for i in p:
                counts[i] += 1

    return [c / samples for c in counts]

# Monznik biasu ludzkiego do losowego roztawienia przeciwnika
def hide_bias(beta=BETA, samples=SAMPLES, rng=None, fleet=DEFAULT_FLEET,
              board_size=BOARD_SIZE):
    hide = hide_occupancy(beta, samples, rng, fleet, board_size)
    uniform = uniform_occupancy(fleet, board_size)

    bias = [h / u for h, u in zip(hide, uniform)]

    mean = sum(bias) / len(bias)
    return [b / mean for b in bias]
