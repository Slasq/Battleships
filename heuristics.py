import random

def random_moves(self):
    search = self.player1.search if self.player1_turn else self.player2.search
    unknown = [i for i, s in enumerate(search) if s == "U"]
    if unknown:
        self.move(random.choice(unknown))

def basic_ai(self):
    search = self.player1.search if self.player1_turn else self.player2.search
    unknown = [i for i, s in enumerate(search) if s == "U"]
    hits = [i for i, s in enumerate(search) if s == "H"]
    if not unknown:
        return

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

    # Hierarhia 
    # Kontynuacja kierunku > sąsiad trafiony> szachownica > losowy
    if len(ns2) > 0:
        self.move(random.choice(ns2))
        return

    if len(ns1) > 0:
        self.move(random.choice(ns1))
        return

    if len(checkerboard) > 0:
        self.move(random.choice(checkerboard))
        return

    # Kiedy nic nie działa
    self.random_moves()
