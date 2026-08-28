ITEMS = [
    ("GRACZ VS AI", "play"),
    ("AI VS AI", "ai_vs_ai"),
    ("USTAWIENIA", "settings"),
    ("WYJDZ", "quit"),
]

READY = {"play", "ai_vs_ai", "settings", "quit"}


class Menu:
    def __init__(self):
        self.selected = 0

    def move(self, step):
        self.selected = (self.selected + step) % len(ITEMS)

    def select(self, index):
        if 0 <= index < len(ITEMS):
            self.selected = index

    def activate(self):
        return ITEMS[self.selected][1]
