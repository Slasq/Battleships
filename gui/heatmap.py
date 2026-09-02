from ml.probmap.solver import probability_map

from .draw import lerp

HEAT_LIFT = 3

HEAT_RAMP = [
    (16, 20, 56),
    (56, 40, 128),
    (128, 48, 144),
    (200, 88, 112),
    (240, 152, 72),
    (255, 232, 160),
]


def normalized_density(search):
    probs = probability_map(search)
    top = max(probs)
    return [v / top for v in probs] if top else [0.0] * len(search)


def heat_color(t):
    t = max(0.0, min(1.0, t))
    seg = t * (len(HEAT_RAMP) - 1)
    i = min(int(seg), len(HEAT_RAMP) - 2)
    return lerp(HEAT_RAMP[i], HEAT_RAMP[i + 1], seg - i)
