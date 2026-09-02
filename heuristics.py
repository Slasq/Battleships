import random


def unknown_cells(search):
    return [i for i, s in enumerate(search) if s == "U"]


def pick_random(search):
    unknown = unknown_cells(search)
    return random.choice(unknown) if unknown else None


def pick_move(search):
    unknown = unknown_cells(search)
    hits = [i for i, s in enumerate(search) if s == "H"]
    if not unknown:
        return None

    hits_set = set(hits)

    checkerboard = []
    for u in unknown:
        row = u // 10
        col = u % 10
        if (row + col) % 2 == 0:
            checkerboard.append(u)

    ns1_set = set()
    for h in hits:
        hr, hc = h // 10, h % 10
        for nr, nc in ((hr - 1, hc), (hr + 1, hc), (hr, hc - 1), (hr, hc + 1)):
            if 0 <= nr < 10 and 0 <= nc < 10:
                idx = nr * 10 + nc
                if search[idx] == "U":
                    ns1_set.add(idx)
    ns1 = list(ns1_set)

    ns2_set = set()
    for u in ns1_set:
        r, c = u // 10, u % 10

        if c <= 7 and (u + 1) in hits_set and (u + 2) in hits_set:
            ns2_set.add(u)
            continue
        if c >= 2 and (u - 1) in hits_set and (u - 2) in hits_set:
            ns2_set.add(u)
            continue
        if r <= 7 and (u + 10) in hits_set and (u + 20) in hits_set:
            ns2_set.add(u)
            continue
        if r >= 2 and (u - 10) in hits_set and (u - 20) in hits_set:
            ns2_set.add(u)
            continue

    ns2 = list(ns2_set)

    if ns2:
        return random.choice(ns2)
    if ns1:
        return random.choice(ns1)
    if checkerboard:
        return random.choice(checkerboard)
    return pick_random(search)


def random_moves(self):
    idx = pick_random(self.player1.search if self.player1_turn else self.player2.search)
    if idx is not None:
        self.move(idx)


def basic_ai(self):
    search = self.player1.search if self.player1_turn else self.player2.search
    idx = pick_move(search)
    if idx is not None:
        self.move(idx)
