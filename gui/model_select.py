from .theme import (
    INK,
    MODEL_GRAY,
    MODEL_GREEN,
    MODEL_RED,
    MODEL_YELLOW,
    PAPER,
)

from ml import policies

MODELS = [

    {
        "name": "BASIC_AI",
        "policy": policies.BASIC,
        "placer": policies.UNIFORM,
        "epochs": "N/A",
        "winrate": "15.0%",
        "eps": "0.00",
        "desc": "Prymitywny bot. Strzela dookola.",
        "sprite": "model_basic.png",
        "scale": 5,
        "rank": 1,
        "color": MODEL_GRAY,
        "anim": "shake",
        "diff": "TEST",
    },
    {
        "name": "PROB_MAP",
        "policy": policies.PROBMAP,
        "placer": policies.UNIFORM,
        "epochs": "N/A",
        "winrate": "45.3%",
        "eps": "0.00",
        "desc": "Uzywa mapy zageszczenia statkow.",
        "sprite": "model_probmap.png",
        "scale": 5,
        "rank": 2,
        "color": MODEL_GREEN,
        "anim": "pulse",
        "diff": "SREDNI",
    },
    {
        "name": "DQN_CORE",
        "policy": policies.DQN,
        "placer": policies.UNIFORM,
        "epochs": "5000",
        "winrate": "58.7%",
        "eps": "0.05",
        "desc": "Siec neuronowa. Uczy sie wzorcow.",
        "sprite": "model_dqn_core.png",
        "scale": 5,
        "rank": 3,
        "color": MODEL_YELLOW,
        "anim": "float",
        "diff": "TRUDNY",
    },
    {
        "name": "COMING_SOON",
        "policy": policies.PROBMAP,
        "placer": policies.UNIFORM,
        "locked": True,
        "epochs": "N/A",
        "winrate": "0.0%",
        "eps": "0.00",
        "desc": "Slot na kolejny model. Wkrotce.",
        "sprite": "model_dqn_epic.png",
        "scale": 4,
        "rank": 4,
        "color": MODEL_GRAY,
        "anim": "kraken",
        "diff": "???",
    },
]

BUTTONS = [("WSTECZ", "back"), ("WYBIERZ", "pick")]

MAX_RANK = 4

MODE_SINGLE = "single"
MODE_DUEL = "duel"

STEPS = {MODE_SINGLE: 1, MODE_DUEL: 2}

PROMPTS = {
    (MODE_SINGLE, 0): "TWOJ PRZECIWNIK",
    (MODE_DUEL, 0): "MODEL GRACZA 1",
    (MODE_DUEL, 1): "MODEL GRACZA 2",
}

DARK_TEXT = (MODEL_GRAY, MODEL_YELLOW)


class ModelSelect:
    def __init__(self):
        self.selected = 1
        self.button = 1
        self.mode = MODE_SINGLE
        self.step = 0
        self.picks = []

    def begin(self, mode):
        self.mode = mode
        self.step = 0
        self.picks = []
        self.button = 1

    def prompt(self):
        return PROMPTS[(self.mode, self.step)]

    def last_step(self):
        return self.step + 1 >= STEPS[self.mode]

    def confirm_label(self):
        if self.locked():
            return "WKROTCE"
        return "START" if self.last_step() else "DALEJ"

    def picked(self):
        return [MODELS[i] for i in self.picks]

    def locked(self):
        return bool(self.current().get("locked"))

    def confirm(self):
        if self.locked():
            return "locked"
        self.picks.append(self.selected)
        if len(self.picks) < STEPS[self.mode]:
            self.step += 1
            return "next"
        return "start"

    def back(self):
        if self.step == 0:
            return "menu"
        self.step -= 1
        self.picks.pop()
        return "step"

    def move(self, step):
        self.selected = (self.selected + step) % len(MODELS)

    def select(self, index):
        if 0 <= index < len(MODELS):
            self.selected = index

    def focus_button(self, index):
        if 0 <= index < len(BUTTONS):
            self.button = index

    def current(self):
        return MODELS[self.selected]

    def accent(self):
        return self.current()["color"]

    def on_accent(self):
        return INK if self.accent() in DARK_TEXT else PAPER

    def activate(self, index=None):
        return BUTTONS[self.button if index is None else index][1]
