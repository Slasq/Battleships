import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import argparse
import random
import statistics

from tqdm import tqdm

import ml.policies as pol
from engine import Game
from ml.probmap.placement import BETA, SAMPLES, hide_bias
from ml.probmap.prior import load_bias
from ml.probmap.solver import HIT_WEIGHT, best_move

# Przebieg
GAMES = 1000 # 1000
FLEET_SEED = 1234 # 1234
POLICY_SEED = 999 # 999

# Rozkład ukrytego roztawienia
BIAS_SEED = 777

# Limit strzałów
MAX_SHOTS = 100


# Jeden ruch solvera
def shoot_probmap(game, rng, bias, hit_weight):
    move = best_move(game.player1.search, rng=rng, hit_weight=hit_weight, bias=bias)
    if move is not None:
        game.move(move)


# Losowa glota przeciwnika
def build_placer(name, beta):
    if name == pol.HIDE:
        return lambda rng: pol.place_hide(rng, beta)

    place = pol.placer(name)
    return lambda rng: place(rng)


# Tablica agentów
def build_agents(policy_rng, human, hide, hit_weight):
    agents = [
        ("random", lambda game: game.random_moves()),
        ("basic_ai", lambda game: game.basic_ai()),
        ("probmap", lambda game: shoot_probmap(game, policy_rng, None, hit_weight)),
        ("probmap+prior", lambda game: shoot_probmap(game, policy_rng, human, hit_weight)),
    ]

    if hide is not None:
        agents.append(
            ("probmap+hide", lambda game: shoot_probmap(game, policy_rng, hide, hit_weight))
        )

    return agents


# Rozegranie jednej partii
def play(fleet_seed, shoot, make_fleet):
    fleet_rng = random.Random(fleet_seed)
    ships = make_fleet(fleet_rng)

    game = Game(human1=False, human2=False, rng=fleet_rng, ships2=ships)
    shots = 0

    while not game.over and shots < MAX_SHOTS:
        # Silnik oddaje ture po pudle
        game.player1_turn = True
        shoot(game)
        shots += 1

    return shots


# Ten sam zestaw flot dla kazdego agenta
def measure(name, shoot, make_fleet, games, fleet_seed):
    shots = []
    for i in tqdm(range(games), desc=f"{name:<14}", unit="gra", leave=False):
        shots.append(play(fleet_seed + i, shoot, make_fleet))
    return shots


def print_header(games, fleet_seed, placer, beta, hit_weight, samples):
    label = pol.PLACER_LABELS[placer]
    if placer == pol.HIDE:
        label += f", beta {beta:g}, rozklad z {samples} flot"

    print()
    print(f"Rozstawienie : {label}")
    print(f"Waga trafien : {hit_weight:g}")
    print(f"Partie       : {games}")
    print(f"Seed floty   : {fleet_seed}")

    if placer != pol.HUMAN:
        print("Uwaga: probmap+prior zaklada rozstawienie ludzkiego")

    print()
    print("=" * 66)
    print(f"{'Agent':<14} | {'Srednia':>7} | {'Mediana':>7} | {'Min':>4} | {'Max':>4} | {'do konca':>8}")
    print("-" * 66)


def print_row(name, shots):
    # Partia bez zatopienia calej floty w limicie pol
    finished = 100.0 * sum(1 for s in shots if s < MAX_SHOTS) / len(shots)

    print(f"{name:<14} | {statistics.mean(shots):>7.1f} | {statistics.median(shots):>7.1f}"
          f" | {min(shots):>4} | {max(shots):>4} | {finished:>7.1f}%")


def parse_args():
    p = argparse.ArgumentParser(description="Pomiar agentow na wspolnym zestawie flot")
    p.add_argument("--games", type=int, default=GAMES, help="liczba partii na agenta")
    p.add_argument("--seed", type=int, default=FLEET_SEED, help="seed zestawu flot")
    p.add_argument("--placer", nargs="+", default=[pol.UNIFORM], choices=list(pol.PLACERS),
                   help="rozstawienia floty przeciwnika")
    p.add_argument("--beta", nargs="+", type=float, default=[BETA],
                   help="sila ukrywania, tylko dla rozstawienia hide")
    p.add_argument("--hit-weight", nargs="+", type=float, default=[HIT_WEIGHT],
                   help="waga trafienia w solverze")
    p.add_argument("--samples", type=int, default=SAMPLES,
                   help="liczba flot na rozklad rozstawien ukrytym")
    return p.parse_args()


def main():
    args = parse_args()

    human = load_bias()
    bias_cache = {}

    for placer in args.placer:
        # Beta rusza tylko przy roztawieniu ukrytym
        betas = args.beta if placer == pol.HIDE else [None]

        for beta in betas:
            make_fleet = build_placer(placer, beta)

            hide = None
            if placer == pol.HIDE:
                if beta not in bias_cache:
                    bias_cache[beta] = hide_bias(beta, args.samples, random.Random(BIAS_SEED))
                hide = bias_cache[beta]

            for hit_weight in args.hit_weight:
                print_header(args.games, args.seed, placer, beta, hit_weight, args.samples)

                agents = build_agents(random.Random(POLICY_SEED), human, hide, hit_weight)
                for name, shoot in agents:
                    shots = measure(name, shoot, make_fleet, args.games, args.seed)
                    print_row(name, shots)

                print("=" * 66)


if __name__ == "__main__":
    main()
