import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import argparse
import random
import statistics

from tqdm import tqdm

from engine import Game
from ml.probmap.prior import load_bias
from ml.probmap.solver import best_move

# Przebieg
GAMES = 1000
FLEET_SEED = 12345
POLICY_SEED = 999

# Limit strzałów
MAX_SHOTS = 100


# Jeden ruch solvera
def shoot_probmap(game, rng, bias):
    move = best_move(game.player1.search, rng=rng, bias=bias)
    if move is not None:
        game.move(move)


# Lista agentow do tabeli
def build_agents(policy_rng, bias):
    return [
        ("random", lambda game: game.random_moves()),
        ("basic_ai", lambda game: game.basic_ai()),
        ("probmap", lambda game: shoot_probmap(game, policy_rng, None)),
        ("probmap+prior", lambda game: shoot_probmap(game, policy_rng, bias)),
    ]


# Jedna partia g1 vs g2
def play(fleet_seed, shoot):
    game = Game(human1=False, human2=False, rng=random.Random(fleet_seed))
    shots = 0

    while not game.over and shots < MAX_SHOTS:
        # Silnik oddaje ture po pudle
        game.player1_turn = True
        shoot(game)
        shots += 1

    return shots


# Ten sam zestaw flot dla kazdego agenta
def measure(name, shoot, games, fleet_seed):
    shots = []
    for i in tqdm(range(games), desc=f"{name:<14}", unit="gra", leave=False):
        shots.append(play(fleet_seed + i, shoot))
    return shots


def print_header(games, fleet_seed):
    print(f"Partie     : {games}")
    print(f"Seed floty : {fleet_seed}")
    print("Rozstawienie: jednostajne z engine")
    print("Uwaga: probmap+prior zaklada rozstawienie ludzkie, wiec tutaj")
    print("       gra przeciw zalozeniu, ktore nie obowiazuje.")
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
    return p.parse_args()


def main():
    args = parse_args()

    bias = load_bias()
    print_header(args.games, args.seed)

    for name, shoot in build_agents(random.Random(POLICY_SEED), bias):
        shots = measure(name, shoot, args.games, args.seed)
        print_row(name, shots)

    print("=" * 66)


if __name__ == "__main__":
    main()
