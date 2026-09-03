import math
import random

from ml.probmap.solver import BOARD_SIZE, CELLS, DEFAULT_FLEET, placements, probability_map

BETA = 2.0
_hide = None


# Przeszukiwanie pustej planszy przedzial 0-1 strzela w najwyszą wartośc
def hide_map():
    global _hide
    if _hide is None:
        raw = probability_map(["U"] * CELLS)
        lo, hi = min(raw), max(raw)
        _hide = [(v - lo) / (hi - lo) for v in raw]
    return _hide

# Roztawienie z losowymi wagami im chlodniej na heatmapie tym chetniej tam postawi
def place(rng=None, beta=BETA, fleet=DEFAULT_FLEET, board_size=BOARD_SIZE):
    if rng is None:
        rng = random

    hide = hide_map()
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
