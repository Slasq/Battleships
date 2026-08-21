import random
import heuristics

class Ship:
    def __init__(self, size):
        self.size = size
        self.orientation = random.choice(["h", "v"])

        # Losowanie pozycji startowej tak aby była na planszy
        if self.orientation == "h":
            self.row = random.randrange(0, 10)
            self.col = random.randrange(0, 10 - self.size + 1)
        else:  # "v"
            self.row = random.randrange(0, 10 - self.size + 1)
            self.col = random.randrange(0, 10)
        self.indexes = self.get_indexes()

    def get_indexes(self):
        start_index = self.row * 10 + self.col

        if self.orientation == "h":
            return [start_index + i for i in range(self.size)]
        
        elif self.orientation == "v":
            return [start_index + i * 10 for i in range(self.size)]


class player:
    def __init__(self):
        self.ships = []
        self.search = ["U" for i in range(100)] # Nieznana pozycja
        self.place_ships(sizes = [5, 4, 3, 3, 2])

    def place_ships(self, sizes):
        for size in sizes: 
            placed = False
            while not placed:
                # Tworzenie nowego statku
                ship = Ship(size)

                # Czy pozycja jest legalna
                placement_legal = True
                for i in ship.indexes:

                    # Index  < 100
                    if i >= 100:
                            placement_legal = False
                            break

                    # Czy poza granicami
                    new_row = i // 10
                    new_col = i % 10

                    # Dodatkowa walidacja indexów
                    if ship.orientation == "h" and new_row != ship.row:
                        placement_legal = False
                        break
                    if ship.orientation == "v" and new_col != ship.col:
                        placement_legal = False
                        break

                    # Czy sie nakladaja
                    for other_ship in self.ships:
                        if i in other_ship.indexes:
                            placement_legal = False
                            break

                    # Ukladanie statkow
                if placement_legal:
                    self.ships.append(ship)
                    placed = True

        self.indexes = [i for ship in self.ships for i in ship.indexes]

    def test_board(self):
        all = [i for ship in self.ships for i in ship.indexes]
        index = ['-' if i not in all else "X" for i in range(100)]
        for row in range(10):
            print(" ".join(index[row * 10 : (row + 1) * 10]))

class Game: 
    def __init__(self, human1, human2):
        self.human1 = human1
        self.human2 = human2
        self.player1 = player()
        self.player2 = player()
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