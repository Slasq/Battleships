from functools import lru_cache

# Plansza z engine
BOARD_SIZE = 10
CELLS = BOARD_SIZE * BOARD_SIZE
DEFAULT_FLEET = (5, 4, 3, 3, 2)

# Ile razy mocniej wazy rozstawienie za kazde pokryte trafienie.
# Duza wartosc sprawia, ze przy odkrytym trafieniu solver sam przechodzi
# w tryb dobijania, bez osobnej galezi hunt/target.
HIT_WEIGHT = 10.0

# Pola zablokowane
BLOCKED = ("M", "S")


# Wszystkie rozstawienia statku danej dlugosci na pustej planszy
@lru_cache(maxsize=None)
def placements(size, board_size=BOARD_SIZE):
    result = []

    # Poziome
    for row in range(board_size):
        for col in range(board_size - size + 1):
            start = row * board_size + col
            result.append(tuple(start + i for i in range(size)))

    # Pionowe
    for row in range(board_size - size + 1):
        for col in range(board_size):
            start = row * board_size + col
            result.append(tuple(start + i * board_size for i in range(size)))

    return tuple(result)

# Szukanie zatopionych pól
def _cover_sunk(cells, sizes, board_size):
    if not cells:
        return []

    # Start od najmniejszej
    target = min(cells)

    # Blokada by nie powtarzac
    for pos, size in enumerate(sizes):
        if size in sizes[:pos]:
            continue

        for placement in placements(size, board_size):
            if target not in placement:
                continue
            if not cells.issuperset(placement):
                continue

            rest = _cover_sunk(cells - set(placement), sizes[:pos] + sizes[pos + 1:], board_size)
            if rest is not None:
                return [size] + rest

    return None


# Siatka dlugosci dla niezabitych statkow
def remaining_sizes(search, fleet=DEFAULT_FLEET, board_size=BOARD_SIZE):
    sunk_cells = {i for i, s in enumerate(search) if s == "S"}
    if not sunk_cells:
        return list(fleet)

    used = _cover_sunk(sunk_cells, tuple(fleet), board_size)

    # Pola s nie są brane pod uwage
    if used is None:
        return list(fleet)

    remaining = list(fleet)
    for size in used:
        remaining.remove(size)
    return remaining

# Mapa wag dla starkows
def probability_map(search, sizes=None, fleet=DEFAULT_FLEET, hit_weight=HIT_WEIGHT):
    board_size = int(round(len(search) ** 0.5))

    if sizes is None:
        sizes = remaining_sizes(search, fleet, board_size)

    weights = [0.0] * len(search)

    for size in sizes:
        for placement in placements(size, board_size):
            hits = 0
            legal = True

            for i in placement:
                state = search[i]
                if state in BLOCKED:
                    legal = False
                    break
                if state == "H":
                    hits += 1

            if not legal:
                continue

            # Waga rozkaladane na pola nietrafione
            weight = hit_weight ** hits
            for i in placement:
                if search[i] == "U":
                    weights[i] += weight

    total = sum(weights)
    if total == 0.0:
        return weights

    return [w / total for w in weights]


# Pole o najwyzszej szansie lub None gdy nie ma gdzie strzelac
def best_move(search, sizes=None, fleet=DEFAULT_FLEET, hit_weight=HIT_WEIGHT, rng=None):
    probs = probability_map(search, sizes, fleet, hit_weight)

    best = max(probs)
    if best == 0.0:
        # Jesli nic nie dziala strzela gdziekolwiek
        unknown = [i for i, s in enumerate(search) if s == "U"]
        if not unknown:
            return None
        return rng.choice(unknown) if rng is not None else unknown[0]

    ties = [i for i, p in enumerate(probs) if p == best]
    return rng.choice(ties) if rng is not None else ties[0]
