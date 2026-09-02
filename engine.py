import random
import heuristics

BOARD = 10
CELLS = BOARD * BOARD
FLEET = [5, 4, 3, 3, 2]


class Ship:
    def __init__(self, size, rng=None, row=None, col=None, orientation=None):
        self.size = size

        # Podane wspolrzedne wygrywaja inaczej losowanie
        if orientation is None:
            # Powtarzalna flota
            if rng is None:
                rng = random

            self.orientation = rng.choice(["h", "v"])

            # Losowanie pozycji startowej
            if self.orientation == "h":
                self.row = rng.randrange(0, BOARD)
                self.col = rng.randrange(0, BOARD - self.size + 1)
            else:  # "v"
                self.row = rng.randrange(0, BOARD - self.size + 1)
                self.col = rng.randrange(0, BOARD)
        else:
            self.orientation = orientation
            self.row = row
            self.col = col

        self.indexes = self.get_indexes()

    def get_indexes(self):
        start_index = self.row * BOARD + self.col

        if self.orientation == "h":
            return [start_index + i for i in range(self.size)]

        elif self.orientation == "v":
            return [start_index + i * BOARD for i in range(self.size)]


# Statek odtworzony z listy pol
def ship_from_cells(cells):
    cells = sorted(cells)
    row = cells[0] // BOARD
    col = cells[0] % BOARD
    orientation = "h" if len(cells) < 2 or cells[1] - cells[0] == 1 else "v"
    return Ship(len(cells), row=row, col=col, orientation=orientation)

def fits(ship, taken):
    if ship.row < 0 or ship.col < 0:
        return False

    for i in ship.indexes:
        if i < 0 or i >= CELLS:
            return False

        # Statek nie moze zawinac wiersza ani kolumny
        if ship.orientation == "h" and i // BOARD != ship.row:
            return False
        if ship.orientation == "v" and i % BOARD != ship.col:
            return False

        # Czy statki nachodza na siebie
        if i in taken:
            return False

    return True


class player:
    def __init__(self, rng = None, ships = None, auto = True):
        self.ships = []
        self.search = ["U" for i in range(CELLS)] # Nieznana pozycja
        self.indexes = []

        # Gotowe roztawienie statkow
        if ships is not None:
            self.set_fleet(ships)
        elif auto:
            self.place_ships(sizes = list(FLEET), rng = rng)

    def add_ship(self, ship):
        if not fits(ship, set(self.indexes)):
            return False

        self.ships.append(ship)
        self.indexes.extend(ship.indexes)
        return True

    def remove_last_ship(self):
        if not self.ships:
            return False

        ship = self.ships.pop()
        for i in ship.indexes:
            self.indexes.remove(i)
        return True

    # Flota jako lista statkow albo jako listy pol
    def set_fleet(self, ships):
        self.ships = []
        self.indexes = []

        for item in ships:
            self.add_ship(item if isinstance(item, Ship) else ship_from_cells(item))

    def place_ships(self, sizes, rng = None):
        for size in sizes:
            placed = False
            while not placed:
                placed = self.add_ship(Ship(size, rng))

    def test_board(self):
        all = [i for ship in self.ships for i in ship.indexes]
        index = ['-' if i not in all else "X" for i in range(100)]
        for row in range(10):
            print(" ".join(index[row * 10 : (row + 1) * 10]))

class Game: 
    def __init__(self, human1, human2, rng = None, ships1 = None, ships2 = None):
        self.human1 = human1
        self.human2 = human2
        self.player1 = player(rng, ships1)
        self.player2 = player(rng, ships2)
        self.player1_turn = True
        self.over = False
        self.result = None
        self.computer_turn = True if not self.human1 else False

    def move(self, i):
        player = self.player1 if self.player1_turn else self.player2
        enemy = self.player2 if self.player1_turn else self.player1
        hit = False

        # Hit "H" or miss "M"
        if i in enemy.indexes:
            player.search[i] = "H"
            hit = True
        else:
            player.search[i] = "M"
        
        # Sprawdza czy jest zatopiony ("S")
        for ship in enemy.ships:
            sunk = True
            for i in ship.indexes:
                if player.search[i] == "U":
                    sunk = False
                    break

            if sunk:
                for i in ship.indexes:
                    player.search[i] = "S"

        # Koniec gry
        game_over = True
        for i in enemy.indexes:
            if player.search[i] == "U":
                game_over = False
        self.over = game_over
        self.result = 1 if self.player1_turn else 2

        # Zmiana tury
        if not hit:
            self.player1_turn = not self.player1_turn
            # Zmiana między komputerem a człowiekiem
            if (self.human1 and not self.human2) or (not self.human1 and self.human2):
                self.computer_turn = not self.computer_turn

    # Wywolanie komputera
    def random_moves(self):
        heuristics.random_moves(self)

    def basic_ai(self):
        heuristics.basic_ai(self)