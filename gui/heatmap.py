from .draw import lerp

FLEET = [5, 4, 3, 3, 2]
HIT_WEIGHT = 12
HEAT_LIFT = 3

HEAT_RAMP = [
    (16, 20, 56),
    (56, 40, 128),
    (128, 48, 144),
    (200, 88, 112),
    (240, 152, 72),
    (255, 232, 160),
]


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


def normalized_density(search):
    raw = density_map(search)
    top = max(raw)
    return [v / top for v in raw] if top else [0.0] * 100


def heat_color(t):
    t = max(0.0, min(1.0, t))
    seg = t * (len(HEAT_RAMP) - 1)
    i = min(int(seg), len(HEAT_RAMP) - 2)
    return lerp(HEAT_RAMP[i], HEAT_RAMP[i + 1], seg - i)
