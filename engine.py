import random

class Ship:
    def __init__(self, size):
        self.row = random.randrange(0, 9)
        self.col = random.randrange(0, 9)
        self.size = size
        self.orientation = random.choice(["h", "v"])
        self.index = self.index()

    def index(self):
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
                for i in ship.index:

                    # Index  < 100
                    if i >= 100:
                            placement_legal = False
                            break

                    # Czy poza granicami
                    new_row = i // 10
                    new_col = i % 10

                    if new_row != ship.row and new_col != ship.col:
                        placement_legal = False
                        break

                    # Czy sie nakladaja
                    for other_ship in self.ships:
                        if i in other_ship.index:
                            placement_legal = False
                            break

                    # Ukladanie statkow
                    if placement_legal:
                        self.ships.append(ship)
                        placed = True

