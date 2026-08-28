import csv
import json
import os

from ml.probmap.solver import BOARD_SIZE, CELLS, DEFAULT_FLEET, placements

# Dane z cliambrown/battleship-data
# Same czestosci pol bez rozstawien
HERE = os.path.dirname(os.path.abspath(__file__))
SQUARES_CSV = os.path.join(HERE, "dataset", "battleship_game_squares.csv")

# Policzony prior lezy obok kodu zeby dzialalo bez csv
PRIOR_JSON = os.path.join(HERE, "human_prior.json")


# Jak czesto ludzie zajmuja kazde pole
# ai_ships 0 to flota czlowieka
# autoplay 0 to gra czlowieka
def human_occupancy(path=SQUARES_CSV, fleet=DEFAULT_FLEET, cells=CELLS):
    counts = [0] * cells

    with open(path, newline="") as handle:
        for row in csv.DictReader(handle):
            if int(row["ai_ships"]) != 0 or int(row["autoplay"]) != 0:
                continue
            counts[int(row["square"]) - 1] += int(row["games"])

    total = sum(counts)
    if total == 0:
        raise ValueError("brak ludzkich rozstawien w " + path)

    # Kazda partia zajmuje sum(fleet) pol wiec stad liczba partii
    games = total / sum(fleet)
    return [c / games for c in counts]


# To samo ale dla losowania jednostajnego
# Statki liczone osobno bez kolizji wiec z grubsza
def uniform_occupancy(fleet=DEFAULT_FLEET, board_size=BOARD_SIZE):
    weights = [0.0] * (board_size * board_size)

    for size in fleet:
        options = placements(size, board_size)
        share = 1.0 / len(options)
        for placement in options:
            for i in placement:
                weights[i] += share

    return weights


# Mnoznik na pole
# Ile razy czesciej stawia tu czlowiek niz losowanie
# Srednia ustawiona na 1.0 wiec mnozenie nie rusza skali mapy
def human_bias(path=SQUARES_CSV, fleet=DEFAULT_FLEET, board_size=BOARD_SIZE):
    cells = board_size * board_size
    human = human_occupancy(path, fleet, cells)
    uniform = uniform_occupancy(fleet, board_size)

    bias = [h / u for h, u in zip(human, uniform)]

    mean = sum(bias) / len(bias)
    return [b / mean for b in bias]


def save_bias(bias, path=PRIOR_JSON):
    with open(path, "w") as handle:
        json.dump({"board_size": BOARD_SIZE, "bias": bias}, handle, indent=1)


# Wczytanie priora a gdy pliku nie ma to liczymy z csv
def load_bias(path=PRIOR_JSON):
    if not os.path.exists(path):
        return human_bias()

    with open(path) as handle:
        return json.load(handle)["bias"]


if __name__ == "__main__":
    bias = human_bias()
    save_bias(bias)

    print("zapisano " + PRIOR_JSON)
    for row in range(BOARD_SIZE):
        print(" ".join(f"{bias[row * BOARD_SIZE + col]:5.2f}" for col in range(BOARD_SIZE)))
