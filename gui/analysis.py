import random

from .heatmap import normalized_density

EPISODES = 15
SAMPLES = 1000
HIST_MIN, HIST_MAX, HIST_STEP = 30, 100, 5

MODEL_NAME = "dqn_main.pth"
MODEL_EPOCHS = 8402
MODEL_GAMMA = 0.90
MODEL_LR = "5e-4"
MODEL_BUFFER = "100k"
MODEL_EPS = 0.05

AVG_DQN = 48.9
AVG_HEURISTIC = 51.4
AVG_RANDOM = 95.3

VIEWS = ["loss", "reward", "shots", "heatmap"]

TITLES = {
    "loss": "STRATA MODELU (LOSS)",
    "reward": "NAGRODA I EPSILON",
    "shots": "ROZKLAD STRZALOW (1000 GIER)",
    "heatmap": "ZAGESZCZENIE (DENSITY)",
}

BUTTONS = [
    ("WYKRES", "STRAT", "view:loss"),
    ("NAGRODA", "EPSILON", "view:reward"),
    ("ROZKLAD", "STRZALOW", "view:shots"),
    ("HEATMAPA", "DENSITY", "view:heatmap"),
    ("WIDOK", None, "toggle:iso"),
    ("WYJDZ", None, "exit"),
]

EXIT_BUTTON = 5
TOGGLE_BUTTON = 4


def _series():
    rng = random.Random(1337)
    out = []
    for i in range(EPISODES):
        out.append(
            {
                "ep": (i + 1) * 100,
                "loss": max(0.1, 2.5 - i * 0.18 + rng.uniform(-0.2, 0.2)),
                "epsilon": max(0.01, 1.0 - i * 0.08),
                "reward": int(-50 + i * 8 + rng.random() * 10),
                "shots": 95.0 - i * 3.2 + rng.uniform(-1.5, 1.5),
                "q_max": 0.8 + i * 0.42 + rng.uniform(-0.3, 0.3),
            }
        )
    return out


def _histogram():
    rng = random.Random(99)
    bins = [0] * ((HIST_MAX - HIST_MIN) // HIST_STEP)
    for _ in range(SAMPLES):
        value = rng.gauss(AVG_DQN, 8.5)
        slot = int((value - HIST_MIN) // HIST_STEP)
        bins[max(0, min(len(bins) - 1, slot))] += 1
    return bins


def _heat():
    rng = random.Random(7)
    search = ["U"] * 100
    for idx in rng.sample(range(100), 22):
        search[idx] = "M"
    for idx in (34, 35, 44):
        search[idx] = "H"
    return normalized_density(search)


class Analysis:
    def __init__(self):
        self.series = _series()
        self.hist = _histogram()
        self.heat = _heat()
        self.view = "loss"
        self.iso = True
        self.selected = 0
        self.hover = None
        self.origin = None

    @property
    def title(self):
        if self.view == "heatmap":
            return f"{TITLES[self.view]} {'[ISO]' if self.iso else '[2D]'}"
        return TITLES[self.view]

    def toggle_available(self):
        return self.view == "heatmap"

    def button_label(self, index):
        head, sub, _ = BUTTONS[index]
        if index == TOGGLE_BUTTON:
            return head, "-> 2D" if self.iso else "-> ISO"
        return head, sub

    def button_active(self, index):
        action = BUTTONS[index][2]
        return action.startswith("view:") and action.split(":")[1] == self.view

    def button_enabled(self, index):
        return index != TOGGLE_BUTTON or self.toggle_available()

    def move(self, dx, dy):
        col, row = self.selected % 3, self.selected // 3
        col = max(0, min(2, col + dx))
        row = max(0, min(1, row + dy))
        self.selected = row * 3 + col

    def activate(self, index=None):
        if index is None:
            index = self.selected
        action = BUTTONS[index][2]
        if action == "exit":
            return "exit"
        if action == "toggle:iso":
            if self.toggle_available():
                self.iso = not self.iso
            return None
        view = action.split(":")[1]
        if view != self.view:
            self.view = view
            self.hover = None
        return None

    def set_hover(self, target):
        self.hover = target

    def terminal_lines(self):
        if self.hover is None:
            return self._summary()
        if self.view == "heatmap":
            return self._heat_lines(self.hover)
        if self.view == "shots":
            return self._hist_lines(self.hover)
        return self._point_lines(self.hover)

    def _summary(self):
        return [
            [(">> MODEL: ", "label"), (MODEL_NAME, "val")],
            [
                ("EPOKI ", "label"),
                (str(MODEL_EPOCHS), "val"),
                ("  BUFOR ", "label"),
                (MODEL_BUFFER, "val"),
                ("  EPS ", "label"),
                (f"{MODEL_EPS:.2f}", "val"),
            ],
            [
                ("GAMMA ", "label"),
                (f"{MODEL_GAMMA:.2f}", "val"),
                ("  LR ", "label"),
                (MODEL_LR, "val"),
                ("  LOSS ", "label"),
                (f"{self.series[-1]['loss']:.3f}", "val"),
            ],
            [],
            [
                ("SR. STRZALY ", "label"),
                (f"{AVG_DQN:.1f}", "high"),
                ("  HEUR ", "label"),
                (f"{AVG_HEURISTIC:.1f}", "val"),
                ("  RND ", "label"),
                (f"{AVG_RANDOM:.1f}", "val"),
            ],
            [("Najedz kursorem na gorny ekran.", "label")],
        ]

    def _point_lines(self, index):
        d = self.series[index]
        reward_key = "high" if d["reward"] > 0 else "warn"
        reward = f"+{d['reward']}" if d["reward"] > 0 else str(d["reward"])
        return [
            [(">> ANALIZA EPIZODU: ", "label"), (str(d["ep"]), "val")],
            [("LOSS (Strata): ", "label"), (f"{d['loss']:.4f}", "val")],
            [("EPSILON (Eksplor.): ", "label"), (f"{d['epsilon']:.2f}", "val")],
            [("SR. NAGRODA: ", "label"), (reward, reward_key)],
            [("SR. STRZALY: ", "label"), (f"{d['shots']:.1f}", "val")],
            [("MAX Q: ", "label"), (f"{d['q_max']:.2f}", "val")],
        ]

    def _hist_lines(self, index):
        low = HIST_MIN + index * HIST_STEP
        count = self.hist[index]
        share = 100.0 * count / SAMPLES
        cumulative = 100.0 * sum(self.hist[: index + 1]) / SAMPLES
        return [
            [(">> PRZEDZIAL: ", "label"), (f"{low}-{low + HIST_STEP - 1} STRZALOW", "val")],
            [],
            [("PARTIE: ", "label"), (f"{count}", "val"), (f"  ({share:.1f}%)", "label")],
            [("SKUMULOWANE: ", "label"), (f"{cumulative:.1f}%", "val")],
            [
                ("WZGLEDEM HEUR: ", "label"),
                (
                    f"{low + HIST_STEP / 2 - AVG_HEURISTIC:+.1f}",
                    "high" if low + HIST_STEP / 2 < AVG_HEURISTIC else "warn",
                ),
            ],
        ]

    def _heat_lines(self, index):
        value = self.heat[index]
        col, row = index % 10, index // 10
        if value >= 0.75:
            status, key = "HOTSPOT", "warn"
        elif value >= 0.35:
            status, key = "WARM", "high"
        else:
            status, key = "ZIMNO", "val"
        return [
            [(">> SEKTOR MAPY: ", "label"), (f"{'ABCDEFGHIJ'[col]}{row + 1}", "val")],
            [],
            [("DENSITY (Q-Value): ", "label"), (f"{value:.3f}", "val")],
            [("KLASYFIKACJA: ", "label"), (f"[{status}]", key)],
            [("RANKING: ", "label"), (f"{self._rank(index)} / 100", "val")],
        ]

    def _rank(self, index):
        better = sum(1 for v in self.heat if v > self.heat[index])
        return better + 1
