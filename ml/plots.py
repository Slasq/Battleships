import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import argparse

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd
import random
import seaborn as sns
from tqdm import tqdm

import ml.policies as pol
from engine import Game
from ml.dqn.train import open_neighbours, rolling_mean
from ml.evaluate import FLEET_SEED, MAX_SHOTS, POLICY_SEED, build_agents, build_placer
from ml.probmap.placement import SAMPLES, hide_bias
from ml.probmap.prior import load_bias
from ml.probmap.solver import BOARD_SIZE, CELLS, HIT_WEIGHT, probability_map

# Katalog na wykresy
PLOTS = os.path.join(os.path.dirname(__file__), "..", "plots")

# Beta
PANEL_BETAS = (2.0, 6.0, 14.0)
CURVE_BETAS = (0.0, 2.0, 6.0, 14.0)

BIAS_SEED = 777

# Agenci bez random i basic_ai
SOLVERS = ("probmap", "probmap+hide", "probmap+prior")

# Kolejnosc wierszy w tabeli
AGENT_ORDER = ("random", "basic_ai", "probmap", "probmap+prior", "probmap+hide")

# Okno sredniej kroczacej na wykresie celnosci
WINDOW = 5


def _grid(values, board_size=BOARD_SIZE):
    return [values[row * board_size:(row + 1) * board_size] for row in range(board_size)]


def _save(fig, name):
    os.makedirs(PLOTS, exist_ok=True)
    path = os.path.normpath(os.path.join(PLOTS, name))

    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)

    print("zapisano " + path)
    return path

def _label(placer, beta):
    if placer == pol.HIDE:
        return f"hide b{beta:g}"
    return pol.PLACER_LABELS[placer]

def figure_heat(samples):
    panels = [("gestosc, pusta plansza", probability_map(["U"] * CELLS), "rocket", None)]
    panels.append(("prior ludzki", load_bias(), "vlag", 1.0))

    for beta in PANEL_BETAS:
        bias = hide_bias(beta, samples, random.Random(BIAS_SEED))
        panels.append((f"ukrywajace, beta {beta:g}", bias, "vlag", 1.0))

    fig, axes = plt.subplots(1, len(panels), figsize=(4.2 * len(panels), 4.4))

    for ax, (title, values, cmap, center) in zip(axes, panels):
        sns.heatmap(_grid(values), ax=ax, cmap=cmap, center=center, square=True,
                    cbar_kws={"shrink": 0.7}, xticklabels=False, yticklabels=False)
        ax.set_title(title)

    fig.suptitle("Mapa gestosci i rozklady rozstawien", y=1.02)
    return _save(fig, "probmap_heatmaps.png")

def _play_traced(fleet_seed, shoot, make_fleet):
    fleet_rng = random.Random(fleet_seed)
    game = Game(human1=False, human2=False, rng=fleet_rng, ships2=make_fleet(fleet_rng))

    hits = []
    adj_ok = 0
    adj_total = 0
    shots = 0

    while not game.over and shots < MAX_SHOTS:
        before = list(game.player1.search)
        neighbours = open_neighbours(before)

        game.player1_turn = True
        shoot(game)
        shots += 1

        after = game.player1.search

        target = None
        for i, state in enumerate(after):
            if before[i] == "U" and state != "U":
                target = i
                break

        hits.append(target is not None and after[target] in ("H", "S"))

        if neighbours:
            adj_total += 1
            if target in neighbours:
                adj_ok += 1

    return shots, hits, adj_ok, adj_total

def collect(games, seed, samples):
    human = load_bias()
    bias_cache = {}

    rows = []
    steps = {}

    plans = [(pol.UNIFORM, None), (pol.HUMAN, None)]
    plans += [(pol.HIDE, beta) for beta in CURVE_BETAS]

    for placer, beta in plans:
        hide = None
        if placer == pol.HIDE:
            if beta not in bias_cache:
                bias_cache[beta] = hide_bias(beta, samples, random.Random(BIAS_SEED))
            hide = bias_cache[beta]

        label = _label(placer, beta)
        make_fleet = build_placer(placer, beta)
        agents = build_agents(random.Random(POLICY_SEED), human, hide, HIT_WEIGHT)

        for name, shoot in agents:
            desc = f"{label:<12} {name:<14}"

            for i in tqdm(range(games), desc=desc, unit="gra", leave=False):
                shots, hits, adj_ok, adj_total = _play_traced(seed + i, shoot, make_fleet)

                rows.append({
                    "placer": placer,
                    "beta": beta,
                    "label": label,
                    "agent": name,
                    "shots": shots,
                    "adj_ok": adj_ok,
                    "adj_total": adj_total,
                })

                for step, hit in enumerate(hits, start=1):
                    key = (label, name, step)
                    bucket = steps.setdefault(key, [0, 0])
                    bucket[0] += int(hit)
                    bucket[1] += 1

    data = pd.DataFrame(rows)

    accuracy = pd.DataFrame(
        [{"label": key[0], "agent": key[1], "step": key[2], "rate": hit / total}
         for key, (hit, total) in steps.items()]
    )

    return data, accuracy

def figure_table(data, games):
    table = data.pivot_table(index="agent", columns="label", values="shots", aggfunc="mean")
    table = table.loc[[a for a in AGENT_ORDER if a in table.index]]

    fig, ax = plt.subplots(figsize=(1.6 * len(table.columns) + 3, 0.7 * len(table) + 2))
    sns.heatmap(table, annot=True, fmt=".1f", cmap="rocket_r", linewidths=0.5,
                cbar_kws={"label": "srednia liczba strzalow"}, ax=ax)

    ax.set_xlabel("rozstawienie floty")
    ax.set_ylabel("")
    ax.set_title(f"Srednia liczba strzalow, {games} partii na pole")

    return _save(fig, "probmap_table_means.png")

def figure_beta(data, games):
    hide = data[data["placer"] == pol.HIDE]
    means = hide.groupby(["beta", "agent"], as_index=False)["shots"].mean()
    lines = means[means["agent"].isin(SOLVERS)]

    fig, ax = plt.subplots(figsize=(7.5, 5))
    sns.lineplot(data=lines, x="beta", y="shots", hue="agent", marker="o", ax=ax)

    bar_basic = means[means["agent"] == "basic_ai"]["shots"].mean()
    bar_random = means[means["agent"] == "random"]["shots"].mean()

    ax.axhline(bar_basic, color="darkgreen", linestyle="--", linewidth=1.5,
               label=f"basic_ai {bar_basic:.1f}")
    ax.axhline(bar_random, color="gray", linestyle=":", linewidth=1.5,
               label=f"random {bar_random:.1f}")

    ax.set_xlabel("beta, sila chowania floty")
    ax.set_ylabel("srednia liczba strzalow")
    ax.set_title(f"Koszt chowania floty, {games} partii na punkt")
    ax.legend()

    return _save(fig, "probmap_beta_curve.png")

def figure_ecdf(data, placer, beta):
    label = _label(placer, beta)
    subset = data[data["label"] == label]

    fig, ax = plt.subplots(figsize=(7.5, 5))
    sns.ecdfplot(data=subset, x="shots", hue="agent", ax=ax)

    ax.set_xlabel("liczba strzalow do zatopienia floty")
    ax.set_ylabel("odsetek partii")
    ax.set_title(f"Rozklad liczby strzalow, rozstawienie {label}")

    return _save(fig, "probmap_shots_ecdf.png")

def figure_spread(data):
    subset = data[data["agent"] != "random"]

    fig, ax = plt.subplots(figsize=(11, 5.5))
    sns.boxplot(data=subset, x="label", y="shots", hue="agent", fliersize=1, ax=ax)

    ax.set_xlabel("rozstawienie floty")
    ax.set_ylabel("liczba strzalow")
    ax.set_title("Rozrzut liczby strzalow w przekrojach")

    return _save(fig, "probmap_shots_spread.png")

def figure_edge(data):
    means = data.groupby(["label", "agent"], as_index=False)["shots"].mean()
    wide = means.pivot(index="label", columns="agent", values="shots")

    edge = wide[[a for a in SOLVERS if a in wide.columns]].sub(wide["basic_ai"], axis=0)
    edge = edge.reset_index().melt(id_vars="label", var_name="agent", value_name="delta")

    fig, ax = plt.subplots(figsize=(9, 5))
    sns.barplot(data=edge, x="label", y="delta", hue="agent", ax=ax)
    ax.axhline(0, color="black", linewidth=1)

    ax.set_xlabel("rozstawienie floty")
    ax.set_ylabel("roznica strzalow wobec basic_ai")
    ax.set_title("Przewaga solvera nad heurystyka, minus znaczy lepiej")

    return _save(fig, "probmap_edge_vs_basic.png")

def figure_accuracy(accuracy, placer, beta):
    label = _label(placer, beta)
    subset = accuracy[accuracy["label"] == label].sort_values("step")

    fig, ax = plt.subplots(figsize=(8.5, 5))

    for agent, chunk in subset.groupby("agent"):
        sns.lineplot(x=chunk["step"], y=rolling_mean(list(chunk["rate"]), WINDOW),
                     ax=ax, label=agent, linewidth=1.6)

    ax.set_xlabel("numer strzalu w partii")
    ax.set_ylabel("szansa trafienia")
    ax.set_title(f"Celnosc w trakcie partii, rozstawienie {label}, srednia z {WINDOW} krokow")
    ax.legend()

    return _save(fig, "probmap_accuracy.png")

def figure_adjacent(data):
    grouped = data.groupby(["label", "agent"], as_index=False)[["adj_ok", "adj_total"]].sum()
    grouped["dobijanie"] = 100.0 * grouped["adj_ok"] / grouped["adj_total"].clip(lower=1)

    fig, ax = plt.subplots(figsize=(10, 5))
    sns.barplot(data=grouped, x="label", y="dobijanie", hue="agent", ax=ax)

    ax.set_xlabel("rozstawienie floty")
    ax.set_ylabel("odsetek krokow")
    ax.set_title("Dobijanie: strzal w sasiada trafienia, gdy taki sasiad istnieje")

    return _save(fig, "probmap_adjacent.png")

def print_table(data, label):
    subset = data[data["label"] == label]

    print("\n" + "=" * 72)
    print(f"Rozstawienie: {label}")
    print(f"{'Agent':<14} | {'Srednia':>8} | {'Min':>5} | {'Max':>5} | {'na 100':>7} | {'dobijanie':>9}")
    print("-" * 72)

    for agent in AGENT_ORDER:
        rows = subset[subset["agent"] == agent]
        if rows.empty:
            continue

        shots = rows["shots"]
        full = 100.0 * (shots >= CELLS).mean()
        adj = 100.0 * rows["adj_ok"].sum() / max(rows["adj_total"].sum(), 1)

        print(f"{agent:<14} | {shots.mean():>8.1f} | {shots.min():>5} | {shots.max():>5}"
              f" | {full:>6.1f}% | {adj:>8.1f}%")

    print("=" * 72)


def parse_args():
    p = argparse.ArgumentParser(description="Wykresy do pomiarow probmapa")
    p.add_argument("figure", choices=["heat", "all"])
    p.add_argument("--games", type=int, default=1000, help="liczba partii na agenta")
    p.add_argument("--seed", type=int, default=FLEET_SEED, help="seed zestawu flot")
    p.add_argument("--samples", type=int, default=SAMPLES,
                   help="liczba flot na rozklad rozstawien chowajacych")
    p.add_argument("--placer", default=pol.UNIFORM, choices=list(pol.PLACERS),
                   help="rozstawienie na wykresach celnosci i rozkladu")
    p.add_argument("--beta", type=float, default=6.0, help="beta na tych wykresach")
    return p.parse_args()


def main():
    args = parse_args()
    sns.set_theme(style="whitegrid")

    figure_heat(args.samples)
    if args.figure == "heat":
        return

    data, accuracy = collect(args.games, args.seed, args.samples)
    beta = args.beta if args.placer == pol.HIDE else None

    figure_table(data, args.games)
    figure_beta(data, args.games)
    figure_ecdf(data, args.placer, beta)
    figure_spread(data)
    figure_edge(data)
    figure_accuracy(accuracy, args.placer, beta)
    figure_adjacent(data)

    for label in data["label"].unique():
        print_table(data, label)


if __name__ == "__main__":
    main()
