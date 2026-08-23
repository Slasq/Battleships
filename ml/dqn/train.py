import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import torch
from tqdm import tqdm

from engine import Game
from ml.dqn.agent import DQNAgent
from ml.dqn.trainer import ReplayBuffer, train_step
from ml.environment import BattleshipEnv

# Przebieg
NUM_EPISODES = 5000
BATCH_SIZE = 512
TRAIN_EVERY = 4
TARGET_SYNC = 1000
SAVE_EVERY = 500

# Feedback
REPORT_EVERY = 250
WINDOW = 50
BASELINE_GAMES = 300
EVAL_GAMES = 200

# Epsilon wywala się pod koniec
EPSILON_START = 1.0
EPSILON_MIN = 0.01
DECAY_SPAN = 0.9

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
TAG = "main"
MODEL_PATH = os.path.join(ROOT, "models", f"dqn_{TAG}.pth")
CHECKPOINT_PATH = os.path.join(ROOT, "models", f"dqn_{TAG}_checkpoint.pth")
PLOT_PATH = os.path.join(ROOT, "plots", f"dqn_{TAG}_training.png")


# Argumenty wiersza polecen
def parse_args():
    p = argparse.ArgumentParser(description="Trening DQN na statkach")
    p.add_argument("--tag", default="main", help="nazwa przebiegu w nazwach plikow")
    p.add_argument("--fresh", action="store_true", help="zignoruj checkpoint")
    return p.parse_args()


# Kazdy przebieg pisze do swoich plikow
def use_tag(tag):
    global TAG, MODEL_PATH, CHECKPOINT_PATH, PLOT_PATH
    TAG = tag
    MODEL_PATH = os.path.join(ROOT, "models", f"dqn_{tag}.pth")
    CHECKPOINT_PATH = os.path.join(ROOT, "models", f"dqn_{tag}_checkpoint.pth")
    PLOT_PATH = os.path.join(ROOT, "plots", f"dqn_{tag}_training.png")


# Tempo spadku rozlozone na DECAY_SPAN przebiegu
def epsilon_decay_for(episodes):
    return (EPSILON_MIN / EPSILON_START) ** (1.0 / (DECAY_SPAN * episodes))


# Srednia kroczaca
def rolling_mean(values, window):
    out = []
    for i in range(1, len(values) + 1):
        chunk = values[max(0, i - window):i]
        out.append(sum(chunk) / len(chunk))
    return out


# Wolne pola obok trafienia, ktore nie zatopilo statku
def open_neighbours(search):
    size = int(len(search) ** 0.5)
    nb = set()
    for idx, cell in enumerate(search):
        if cell != "H":
            continue
        row, col = divmod(idx, size)
        for r, c in ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)):
            if 0 <= r < size and 0 <= c < size and search[r * size + c] == "U":
                nb.add(r * size + c)
    return nb


# baseline do przebicia
def baseline(num_games, policy):
    shots = []
    for _ in tqdm(range(num_games), desc=f"Poprzeczka {policy}", unit="gra", leave=False):
        game = Game(human1=False, human2=False)
        count = 0
        while not game.over:
            game.player1_turn = True
            if policy == "basic_ai":
                game.basic_ai()
            else:
                game.random_moves()
            count += 1
        shots.append(count)
    return float(np.mean(shots))


# Pelny stany treningowe
def save_checkpoint(path, agent, episode, shot_history, loss_history, steps_done):
    torch.save(
        {
            "episode": episode,
            "policy": agent.policy_net.state_dict(),
            "target": agent.target_net.state_dict(),
            "optimizer": agent.optimizer.state_dict(),
            "epsilon": agent.epsilon,
            "learn_steps": agent.learn_steps,
            "steps_done": steps_done,
            "shot_history": shot_history,
            "loss_history": loss_history,
        },
        path,
    )

def load_checkpoint(path, agent):
    ckpt = torch.load(path, map_location=agent.device, weights_only=False)

    # Stary checkpoint nie pasuje do glowicy dueling
    try:
        agent.policy_net.load_state_dict(ckpt["policy"])
        agent.target_net.load_state_dict(ckpt["target"])
    except RuntimeError as err:
        raise SystemExit(f"Checkpoint {path} nie pasuje do sieci.\n{err}\n"
                         f"Uruchom z --fresh albo z innym --tag.")

    agent.optimizer.load_state_dict(ckpt["optimizer"])
    agent.epsilon = ckpt["epsilon"]
    agent.learn_steps = ckpt.get("learn_steps", 0)
    return (ckpt["episode"], ckpt["shot_history"], ckpt["loss_history"],
            ckpt.get("steps_done", 0))

# Zwraca liczbe strzalow i srednia strat na jeden epizod
def run_episode(env, agent, buffer, batch_size, train_every, steps_done):
    state, _ = env.reset()
    done = False
    ep_loss = []

    while not done:

        # Maska z env
        mask = env.get_valid_actions()
        action = agent.select_action(state, mask)

        next_state, reward, terminated, truncated, _ = env.step(action)
        done = terminated or truncated

        # Zwrocenie terminated do zakonczenia epizodu
        buffer.push(state, action, reward, next_state, float(terminated),
                    env.get_valid_actions())
        state = next_state

        # Licznik krokow gradientu co kazdy stral z train_event
        steps_done += 1
        if steps_done % train_every == 0:
            loss = train_step(agent, buffer, batch_size)
            if loss is not None:
                ep_loss.append(loss)

    avg_loss = sum(ep_loss) / len(ep_loss) if ep_loss else None
    return env.total_shots, avg_loss, steps_done


# Ustawienia przebiegu na wejsciu
def print_header(agent):
    print(f"Urzadzenie : {agent.device}")
    print(f"Epizody    : {NUM_EPISODES}")
    print(f"Gradient   : batch {BATCH_SIZE}, krok co {TRAIN_EVERY} strzalow")
    print(f"Siec celu  : kopia wag co {TARGET_SYNC} krokow gradientu")
    print(f"Gamma      : {agent.gamma}")
    print(f"Epsilon    : {EPSILON_START} do {EPSILON_MIN} przez "
          f"{int(DECAY_SPAN * NUM_EPISODES)} epizodow")
    print(f"Model      : {os.path.normpath(MODEL_PATH)}")
    print()


# Podsumowanie
def report(ep, agent, buffer, shot_history, loss_history, bar_basic, prev_mean):
    window = shot_history[-REPORT_EVERY:]
    mean = sum(window) / len(window)

    losses = [x for x in loss_history[-REPORT_EVERY:] if x is not None]
    loss_txt = f"{sum(losses) / len(losses):.4f}" if losses else "brak"

    trend = "" if prev_mean is None else f" | zmiana {mean - prev_mean:+.1f}"

    tqdm.write(
        f"ep {ep:>5}/{NUM_EPISODES} | srednia {mean:>5.1f} | min {min(window):>3}"
        f" | max {max(window):>3} | do basic_ai {mean - bar_basic:+.1f}"
        f" | loss {loss_txt} | eps {agent.epsilon:.3f} | bufor {len(buffer)}{trend}"
    )
    return mean


def plot(shot_history, loss_history, bar_random, bar_basic):
    sns.set_theme(style="whitegrid")
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    episodes = list(range(1, len(shot_history) + 1))

    # Surowe epizody
    sns.lineplot(x=episodes, y=shot_history, ax=ax1, alpha=0.25,
                 linewidth=0.6, color="steelblue")
    sns.lineplot(x=episodes, y=rolling_mean(shot_history, 100), ax=ax1,
                 linewidth=2, color="crimson", label="srednia 100")

    # Progi
    ax1.axhline(bar_basic, color="darkgreen", linestyle="--", linewidth=1.5,
                label=f"basic_ai {bar_basic:.1f}")
    ax1.axhline(bar_random, color="gray", linestyle=":", linewidth=1.5,
                label=f"random {bar_random:.1f}")

    ax1.set_xlabel("Epizod")
    ax1.set_ylabel("Liczba strzalow")
    ax1.set_title("Strzaly na wygrana")
    ax1.legend()

    # Epizody bez treningu nie maja strat
    losses = [(i + 1, x) for i, x in enumerate(loss_history) if x is not None]
    if losses:
        sns.lineplot(x=[i for i, _ in losses], y=[x for _, x in losses], ax=ax2,
                     alpha=0.7, linewidth=0.8, color="darkorange")
        ax2.set_xlabel("Epizod")
        ax2.set_ylabel("Strata")
        ax2.set_title("Strata DQN")

    plt.tight_layout()
    plt.savefig(PLOT_PATH, dpi=150)
    plt.close()
    print(f"Wykres: {PLOT_PATH}")


# Porownanie z heurystyka
def quick_eval(agent, bar_random, bar_basic):
    print(f"\nEwaluacja ({EVAL_GAMES} gier)...")

    old_eps = agent.epsilon
    agent.epsilon = 0.0

    env = BattleshipEnv()
    shots = []
    adj_ok, adj_total = 0, 0
    for _ in tqdm(range(EVAL_GAMES), desc="DQN eval", unit="gra", leave=False):
        state, _ = env.reset()
        done = False
        while not done:
            search = list(env.get_search())
            mask = env.get_valid_actions()
            action = agent.select_action(state, mask)

            # Agent sprawdza sasiada gdy trafi
            nb = open_neighbours(search)
            if nb:
                adj_total += 1
                if action in nb:
                    adj_ok += 1

            state, _, terminated, truncated, _ = env.step(action)
            done = terminated or truncated
        shots.append(env.total_shots)

    agent.epsilon = old_eps

    print_table(shots, bar_random, bar_basic, adj_ok, adj_total, env.cells)


# Tabela koncowa plus diagnostyka trybu dobijania
def print_table(shots, bar_random, bar_basic, adj_ok, adj_total, cells):
    full = 100.0 * sum(1 for s in shots if s >= cells) / len(shots)
    adj = 100.0 * adj_ok / max(adj_total, 1)

    print("\n" + "=" * 56)
    print(f"{'Agent':<12} | {'Srednia':>8} | {'Min':>5} | {'Max':>5} | {'na 100':>7}")
    print("-" * 56)
    print(f"{'DQN':<12} | {np.mean(shots):>8.1f} | {min(shots):>5} | {max(shots):>5} | {full:>6.1f}%")
    print(f"{'basic_ai':<12} | {bar_basic:>8.1f} | {'':>5} | {'':>5} | {'':>7}")
    print(f"{'random':<12} | {bar_random:>8.1f} | {'':>5} | {'':>5} | {'':>7}")
    print("-" * 56)
    print(f"Dobijanie    : strzal w sasiada H w {adj:.1f}% krokow z wolnym sasiadem")
    print(f"Takich krokow: {adj_total}, czyli {adj_total / len(shots):.1f} na gre")
    print("=" * 56)


def main():
    args = parse_args()
    use_tag(args.tag)

    env = BattleshipEnv()
    agent = DQNAgent(
        epsilon=EPSILON_START,
        epsilon_min=EPSILON_MIN,
        epsilon_decay=epsilon_decay_for(NUM_EPISODES),
        target_sync=TARGET_SYNC,
    )
    buffer = ReplayBuffer()

    print_header(agent)

    # Start od nowa
    start_ep = 1
    steps_done = 0
    shot_history, loss_history = [], []
    if os.path.exists(CHECKPOINT_PATH) and not args.fresh:
        last_ep, shot_history, loss_history, steps_done = load_checkpoint(CHECKPOINT_PATH, agent)
        start_ep = last_ep + 1
        print(f"Checkpoint : wznowienie od epizodu {start_ep}, epsilon {agent.epsilon:.3f}")
        print("Bufor startuje pusty, wiec pierwsze epizody po wznowieniu nie ucza")
        print()

    # Bramka do poprawienia wydjanosci (by nie liczylo 4h)
    if start_ep > NUM_EPISODES:
        print("Przebieg juz skonczony. Uruchom z --fresh albo z innym --tag.")
        return

    print("Liczenie poprzeczki...")
    bar_random = baseline(BASELINE_GAMES, "random")
    bar_basic = baseline(BASELINE_GAMES, "basic_ai")
    print(f"random   : {bar_random:.1f} strzalow")
    print(f"basic_ai : {bar_basic:.1f} strzalow")
    print()

    prev_mean = None
    pbar = tqdm(range(start_ep, NUM_EPISODES + 1), desc=f"DQN [{TAG}]", unit="ep",
                initial=start_ep - 1, total=NUM_EPISODES)

    for ep in pbar:
        shots, avg_loss, steps_done = run_episode(env, agent, buffer, BATCH_SIZE,
                                                  TRAIN_EVERY, steps_done)

        shot_history.append(shots)
        loss_history.append(avg_loss)
        agent.decay_epsilon()

        # Progress bar
        window = shot_history[-WINDOW:]
        pbar.set_postfix(
            srednia=f"{sum(window) / len(window):.1f}",
            eps=f"{agent.epsilon:.3f}",
            loss="brak" if avg_loss is None else f"{avg_loss:.3f}",
            bufor=len(buffer),
            kroki=agent.learn_steps,
        )

        if ep % REPORT_EVERY == 0:
            prev_mean = report(ep, agent, buffer, shot_history, loss_history,
                               bar_basic, prev_mean)

        if ep % SAVE_EVERY == 0:
            agent.save(MODEL_PATH)
            save_checkpoint(CHECKPOINT_PATH, agent, ep, shot_history, loss_history, steps_done)

    pbar.close()

    agent.save(MODEL_PATH)
    save_checkpoint(CHECKPOINT_PATH, agent, NUM_EPISODES, shot_history, loss_history, steps_done)
    print(f"\nTrening skonczony. Krokow gradientu: {agent.learn_steps}")
    print(f"Model: {os.path.normpath(MODEL_PATH)}")

    plot(shot_history, loss_history, bar_random, bar_basic)
    quick_eval(agent, bar_random, bar_basic)


if __name__ == "__main__":
    main()
