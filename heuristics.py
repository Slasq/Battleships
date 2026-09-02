import random


# Pola jeszcze nieostrzelane
def unknown_cells(search):
    return [i for i, s in enumerate(search) if s == "U"]


# Strzal na slepo
def pick_random(search):
    unknown = unknown_cells(search)
    return random.choice(unknown) if unknown else None


# Hunt and target: dobija trafienia, inaczej przeczesuje plansze
def pick_move(search):
    unknown = unknown_cells(search)
    hits = [i for i, s in enumerate(search) if s == "H"]
    if not unknown:
        return None

    hits_set = set(hits)

    # Szachownica co drugi indeks
    checkerboard = []
    for u in unknown:
        row = u // 10
        col = u % 10
        if (row + col) % 2 == 0:
            checkerboard.append(u)

    # Nieznane pola sąsiadujące z trafieniami
    ns1_set = set()
    for h in hits:
        hr, hc = h // 10, h % 10
        for nr, nc in ((hr - 1, hc), (hr + 1, hc), (hr, hc - 1), (hr, hc + 1)):
            if 0 <= nr < 10 and 0 <= nc < 10:
                idx = nr * 10 + nc
                if search[idx] == "U":
                    ns1_set.add(idx)
    ns1 = list(ns1_set)

    # Nieznane pola z dwoma trafieniami w linii (poziom 2)
    ns2_set = set()
    for u in ns1_set:
        r, c = u // 10, u % 10

        # Dwa trafienia w prawo: u+1 i u+2
        if c <= 7 and (u + 1) in hits_set and (u + 2) in hits_set:
            ns2_set.add(u)
            continue
        # Dwa trafienia w lewo: u-1 i u-2
        if c >= 2 and (u - 1) in hits_set and (u - 2) in hits_set:
            ns2_set.add(u)
            continue
        # Dwa trafienia w dół: u+10 i u+20
        if r <= 7 and (u + 10) in hits_set and (u + 20) in hits_set:
            ns2_set.add(u)
            continue
        # Dwa trafienia w górę: u-10 i u-20
        if r >= 2 and (u - 10) in hits_set and (u - 20) in hits_set:
            ns2_set.add(u)
            continue

    ns2 = list(ns2_set)

    # Hierarchia
    # Kontynuacja kierunku > sąsiad trafiony > szachownica > losowy
    if ns2:
        return random.choice(ns2)
    if ns1:
        return random.choice(ns1)
    if checkerboard:
        return random.choice(checkerboard)
    # Kiedy nic nie działa
    return pick_random(search)


# Opakowania na obiekt Game, uzywa ich engine
def random_moves(self):
    idx = pick_random(self.player1.search if self.player1_turn else self.player2.search)
    if idx is not None:
        self.move(idx)


def basic_ai(self):
    search = self.player1.search if self.player1_turn else self.player2.search
    idx = pick_move(search)
    if idx is not None:
        self.move(idx)
