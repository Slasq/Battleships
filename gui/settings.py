import json
from pathlib import Path

import pygame

CONFIG_PATH = Path(__file__).resolve().parent.parent / "settings.json"

OPTIONS = [
    {
        "key": "speed",
        "label": "TEMPO AI",
        "desc": "Jak dlugo agent czeka przed swoim ruchem.",
        "values": [("WOLNE", 1.8), ("NORMALNE", 1.0), ("SZYBKIE", 0.5), ("TURBO", 0.2)],
        "default": 1,
    },
    {
        "key": "heatmap",
        "label": "HEATMAPA",
        "desc": "Mapa zageszczenia statkow widoczna od startu partii.",
        "values": [("WYL", False), ("WL", True)],
        "default": 0,
    },
    {
        "key": "iso",
        "label": "WIDOK PLANSZY",
        "desc": "Rzut izometryczny albo plaska siatka w analizie.",
        "values": [("ISO 3D", True), ("PLASKI 2D", False)],
        "default": 0,
    },
    {
        "key": "anim",
        "label": "ANIMACJE",
        "desc": "Fale, chmury i ruch modeli w menu.",
        "values": [("WL", True), ("WYL", False)],
        "default": 0,
    },
    {
        "key": "scale",
        "label": "SKALA OKNA",
        "desc": "Powiekszenie ekranow. AUTO dopasowuje do pulpitu.",
        "values": [("AUTO", 0), ("x2", 2), ("x3", 3), ("x4", 4)],
        "default": 0,
    },
]

BUTTONS = [("WSTECZ", "back"), ("DOMYSLNE", "reset")]

BY_KEY = {opt["key"]: i for i, opt in enumerate(OPTIONS)}
BUTTON_ROW = len(OPTIONS)


class Settings:
    def __init__(self):
        self.picks = [opt["default"] for opt in OPTIONS]
        self.selected = 0
        self.button = 0
        self.load()

    def value(self, key):
        row = BY_KEY[key]
        return OPTIONS[row]["values"][self.picks[row]][1]

    def label(self, key):
        row = BY_KEY[key]
        return OPTIONS[row]["values"][self.picks[row]][0]

    def value_label(self, row):
        return OPTIONS[row]["values"][self.picks[row]][0]

    def value_index(self, row):
        return self.picks[row]

    @property
    def on_buttons(self):
        return self.selected == BUTTON_ROW

    def move(self, step):
        self.selected = (self.selected + step) % (len(OPTIONS) + 1)

    def select(self, row):
        if 0 <= row <= BUTTON_ROW:
            self.selected = row

    def focus_button(self, index):
        if 0 <= index < len(BUTTONS):
            self.selected = BUTTON_ROW
            self.button = index

    def cycle(self, step, row=None):
        if row is None:
            row = self.selected
        if row == BUTTON_ROW:
            self.button = (self.button + step) % len(BUTTONS)
            return
        values = OPTIONS[row]["values"]
        self.picks[row] = (self.picks[row] + step) % len(values)

    def activate(self, index=None):
        if index is not None:
            self.button = index
            return BUTTONS[index][1]
        if self.on_buttons:
            return BUTTONS[self.button][1]
        self.cycle(1)
        return None

    def reset(self):
        self.picks = [opt["default"] for opt in OPTIONS]

    def preview_row(self):
        return min(self.selected, BUTTON_ROW - 1)

    def preview(self):
        return OPTIONS[self.preview_row()]

    def to_dict(self):
        return {opt["key"]: self.picks[i] for i, opt in enumerate(OPTIONS)}

    def save(self):
        try:
            CONFIG_PATH.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")
        except OSError:
            pass

    def load(self):
        try:
            data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return
        if not isinstance(data, dict):
            return
        for i, opt in enumerate(OPTIONS):
            pick = data.get(opt["key"])
            if isinstance(pick, int) and 0 <= pick < len(opt["values"]):
                self.picks[i] = pick


SETTINGS = Settings()


def anim_ticks():
    return pygame.time.get_ticks() if SETTINGS.value("anim") else 0


def scaled_ms(ms):
    return int(ms * SETTINGS.value("speed"))
