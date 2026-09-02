from .heatmap import normalized_density
from .settings import SETTINGS

VIEWS = ["accuracy", "timeline", "fleet", "map", "timelapse"]

TITLES = {
    "accuracy": "CELNOSC NARASTAJACO",
    "timeline": "PRZEBIEG PARTII",
    "fleet": "ZATAPIANIE FLOTY",
    "map": "MAPA STRZALOW",
    "timelapse": "TIMELAPSE PRZEKONAN",
}

BUTTONS = [
    ("CELNOSC", "PROCENT", "view:accuracy"),
    ("PRZEBIEG", "PARTII", "view:timeline"),
    ("FLOTA", "ZATOPIENIA", "view:fleet"),
    ("MAPA", "STRZALOW", "view:map"),
    ("TIMELAPSE", "HEATMAPY", "view:timelapse"),
    ("WYJDZ", None, "exit"),
]

EXIT_BUTTON = 5
MAP_VIEWS = ("map", "timelapse")

HIT_RESULTS = ("H", "S")

FRAME_MS = 150
LOOP_PAUSE_MS = 1200


class SideStats:
    def __init__(self, name, entries, fleet):
        self.name = name
        self.shots = entries
        self.hits = sum(1 for e in entries if e["res"] in HIT_RESULTS)
        self.accuracy = self.hits / len(entries) if entries else 0.0
        self.cum = self._cumulative()
        self.streak = self._streak()
        self.board = {e["idx"]: e for e in entries}
        self.fleet = self._fleet(fleet)
        self.sunk = sum(1 for _, shot in self.fleet if shot is not None)
        self._density = {}

    def search_at(self, frame):
        search = ["U"] * 100
        for entry in self.shots[:frame]:
            if entry["res"] == "S" and entry["cells"]:
                for cell in entry["cells"]:
                    search[cell] = "S"
            else:
                search[entry["idx"]] = entry["res"]
        return search

    def density_at(self, frame):
        cached = self._density.get(frame)
        if cached is None:
            cached = normalized_density(self.search_at(frame))
            self._density[frame] = cached
        return cached

    def sunk_until(self, frame):
        return sum(1 for _, shot in self.fleet if shot is not None and shot <= frame)

    def _cumulative(self):
        out, hits = [], 0
        for i, entry in enumerate(self.shots):
            if entry["res"] in HIT_RESULTS:
                hits += 1
            out.append(hits / (i + 1))
        return out

    def _streak(self):
        best = run = 0
        for entry in self.shots:
            run = run + 1 if entry["res"] in HIT_RESULTS else 0
            best = max(best, run)
        return best

    def _fleet(self, sizes):
        sunk_at = {}
        for i, entry in enumerate(self.shots):
            if entry["sunk"] is not None:
                sunk_at[entry["sunk"]] = i + 1
        return [(size, sunk_at.get(pos)) for pos, size in enumerate(sizes)]


class Report:
    def __init__(self, match):
        names = match.side_names()
        self.mode = match.mode
        self.over = match.game.over
        self.winner = match.winner() if match.game.over else None
        self.total = len(match.log)
        self.sides = [
            SideStats(
                names[side],
                [e for e in match.log if e["side"] == side],
                match.fleet_sizes(side),
            )
            for side in (0, 1)
        ]

    @property
    def longest(self):
        return max(len(s.shots) for s in self.sides)

    def side_of(self, name):
        return 0 if self.sides[0].name == name else 1


class Analysis:
    def __init__(self):
        self.report = None
        self.view = "accuracy"
        self.iso = SETTINGS.value("iso")
        self.selected = 0
        self.hover = None
        self.frame = 0
        self.playing = True
        self.tl_side = 0
        self._timer = 0

    def load(self, match):
        self.report = Report(match) if match.log else None
        self.iso = SETTINGS.value("iso")
        self.hover = None
        self.frame = 0
        self.playing = True
        self._timer = 0

    @property
    def frames(self):
        if not self.has_data:
            return 0
        return len(self.report.sides[self.tl_side].shots)

    def tick(self, dt):
        if not self.has_data or self.view != "timelapse" or not self.playing:
            return
        self._timer += dt
        step = LOOP_PAUSE_MS if self.frame >= self.frames else FRAME_MS
        if self._timer >= step:
            self._timer = 0
            self.frame = 0 if self.frame >= self.frames else self.frame + 1

    def scrub(self, frame):
        self.frame = max(0, min(self.frames, frame))
        self.playing = False
        self._timer = 0

    def set_iso(self, iso):
        self.iso = iso

    def set_side(self, side):
        if side != self.tl_side:
            self.tl_side = side
            self.frame = min(self.frame, self.frames)

    @property
    def has_data(self):
        return self.report is not None

    @property
    def title(self):
        return TITLES[self.view]

    def has_tabs(self):
        return self.has_data and self.view in MAP_VIEWS

    def button_label(self, index):
        head, sub, _ = BUTTONS[index]
        return head, sub

    def button_active(self, index):
        action = BUTTONS[index][2]
        return action.startswith("view:") and action.split(":")[1] == self.view

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
        view = action.split(":")[1]
        if view != self.view:
            self.view = view
            self.hover = None
            if view == "timelapse":
                self.frame = 0
                self.playing = True
                self._timer = 0
        return None

    def set_hover(self, target):
        self.hover = target
        if self.view != "timelapse":
            return
        if target and target[0] == "frame":
            self.scrub(target[1])
        elif target is None:
            self.playing = True

    def terminal_lines(self):
        if not self.has_data:
            return [
                [(">> BRAK DANYCH", "warn")],
                [],
                [("Rozegraj partie, potem wroc tutaj.", "label")],
                [("Menu: GRACZ VS AI albo AI VS AI.", "label")],
            ]
        if self.view == "timelapse":
            return self._timelapse_lines()
        if self.hover is None:
            return self._summary()
        kind = self.hover[0]
        if kind == "shot":
            return self._shot_lines(*self.hover[1:])
        if kind == "ship":
            return self._ship_lines(*self.hover[1:])
        if kind == "cell":
            return self._cell_lines(*self.hover[1:])
        return self._turn_lines(self.hover[1])

    def _summary(self):
        report = self.report
        a, b = report.sides
        head = f"{a.name} vs {b.name}"
        if report.over:
            outcome = [
                ("ZWYCIEZCA: ", "label"),
                (report.winner, "high"),
                (f"  ({report.total} strzalow)", "label"),
            ]
        else:
            outcome = [("PARTIA W TOKU", "warn"), (f"  ({report.total} strzalow)", "label")]
        return [
            [(">> PARTIA: ", "label"), (head, "val")],
            outcome,
            [],
            [
                (f"{a.name:<6}", "val"),
                (" STRZ ", "label"),
                (f"{len(a.shots):<3}", "val"),
                (" TRAF ", "label"),
                (f"{a.hits:<3}", "val"),
                (" CEL ", "label"),
                (f"{a.accuracy * 100:.1f}%", "high"),
            ],
            [
                (f"{b.name:<6}", "val"),
                (" STRZ ", "label"),
                (f"{len(b.shots):<3}", "val"),
                (" TRAF ", "label"),
                (f"{b.hits:<3}", "val"),
                (" CEL ", "label"),
                (f"{b.accuracy * 100:.1f}%", "high"),
            ],
            [
                ("SERIA ", "label"),
                (f"{a.streak}/{b.streak}", "val"),
                ("   FLOTA ", "label"),
                (f"{a.sunk}/5 : {b.sunk}/5", "val"),
            ],
        ]

    def _timelapse_lines(self):
        side = self.report.sides[self.tl_side]
        frame = min(self.frame, len(side.shots))
        density = side.density_at(frame)
        search = side.search_at(frame)
        unknown = sum(1 for s in search if s == "U")
        best = max(range(100), key=lambda i: density[i])
        state = "PAUZA" if not self.playing else "GRA"

        lines = [
            [
                (">> KLATKA: ", "label"),
                (f"{frame}/{len(side.shots)}", "val"),
                ("   ", "label"),
                (side.name, "high"),
                (f"   [{state}]", "label"),
            ],
            [],
        ]
        if frame == 0:
            lines.append([("START: ", "label"), ("plansza nieodkryta", "val")])
        else:
            entry = side.shots[frame - 1]
            lines.append(
                [
                    ("STRZAL: ", "label"),
                    (_coord(entry["idx"]), "val"),
                    ("  ", "label"),
                    (_result_name(entry["res"]), _result_key(entry["res"])),
                ]
            )
        lines.append(
            [
                ("NIEZNANE: ", "label"),
                (f"{unknown}", "val"),
                ("   ZATOPIL: ", "label"),
                (f"{side.sunk_until(frame)}/5", "val"),
            ]
        )
        lines.append(
            [
                ("NAJGORETSZE: ", "label"),
                (_coord(best), "warn"),
                (f"  ({density[best]:.2f})", "label"),
            ]
        )
        lines.append([("Najedz na os czasu aby przewijac.", "label")])
        return lines

    def _turn_lines(self, index):
        lines = [[(">> STRZAL NR: ", "label"), (str(index + 1), "val")], []]
        for side in self.report.sides:
            if index < len(side.cum):
                entry = side.shots[index]
                lines.append(
                    [
                        (f"{side.name:<6} ", "label"),
                        (f"{side.cum[index] * 100:5.1f}%", "val"),
                        ("  " + _result_name(entry["res"]), _result_key(entry["res"])),
                    ]
                )
            else:
                lines.append([(f"{side.name:<6} ", "label"), ("koniec gry", "label")])
        return lines

    def _shot_lines(self, side_index, shot_index):
        side = self.report.sides[side_index]
        entry = side.shots[shot_index]
        lines = [
            [(">> ", "label"), (side.name, "val"), (f", strzal {shot_index + 1}", "label")],
            [],
            [("POLE: ", "label"), (_coord(entry["idx"]), "val")],
            [("WYNIK: ", "label"), (_result_name(entry["res"]), _result_key(entry["res"]))],
            [("CELNOSC PO: ", "label"), (f"{side.cum[shot_index] * 100:.1f}%", "val")],
        ]
        if entry["sunk_size"] is not None:
            lines.append([("ZATOPIL STATEK: ", "label"), (f"{entry['sunk_size']} pol", "high")])
        return lines

    def _ship_lines(self, side_index, ship_index):
        side = self.report.sides[side_index]
        size, shot = side.fleet[ship_index]
        if shot is None:
            return [
                [(">> STATEK: ", "label"), (f"{size} pol", "val")],
                [],
                [("STATUS: ", "label"), ("NIEZATOPIONY", "warn")],
                [(f"Flota {side.name}: ", "label"), (f"{side.sunk}/5", "val")],
            ]
        order = sorted(s for _, s in side.fleet if s is not None).index(shot) + 1
        return [
            [(">> STATEK: ", "label"), (f"{size} pol", "val")],
            [],
            [("ZATOPIONY PRZY: ", "label"), (f"{shot} strzale", "val")],
            [("KOLEJNOSC: ", "label"), (f"{order} z {side.sunk}", "val")],
            [("STRZELAL: ", "label"), (side.name, "high")],
        ]

    def _cell_lines(self, side_index, index):
        side = self.report.sides[side_index]
        entry = side.board.get(index)
        head = [(">> SEKTOR: ", "label"), (_coord(index), "val")]
        if entry is None:
            return [
                head,
                [],
                [("STATUS: ", "label"), ("NIEOSTRZELANE", "label")],
                [(f"Plansza: {side.name}", "label")],
            ]
        return [
            head,
            [],
            [("STRZELAL: ", "label"), (side.name, "val")],
            [("STRZAL NR: ", "label"), (str(side.shots.index(entry) + 1), "val")],
            [("WYNIK: ", "label"), (_result_name(entry["res"]), _result_key(entry["res"]))],
        ]


def _coord(index):
    return f"{'ABCDEFGHIJ'[index % 10]}{index // 10 + 1}"


def _result_name(res):
    if res == "M":
        return "PUDLO"
    if res == "S":
        return "ZATOPIONY"
    return "TRAFIENIE"


def _result_key(res):
    if res == "M":
        return "label"
    if res == "S":
        return "high"
    return "warn"
