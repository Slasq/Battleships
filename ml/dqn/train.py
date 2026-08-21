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
TARGET_UPDATE = 100
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
MODEL_PATH = os.path.join(ROOT, "models", "dqn_latest.pth")
CHECKPOINT_PATH = os.path.join(ROOT, "models", "dqn_checkpoint.pth")
PLOT_PATH = os.path.join(ROOT, "plots", "dqn_training.png")


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


# baseline do przebicia
def baseline(num_games, policy):
    shots = []
    for _ in tqdm(range(num_games), desc=f"Poprzeczka {policy}", leave=False):
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
def save_checkpoint(path, agent, episode, shot_history, loss_history):
    torch.save(
        {
            "episode": episode,
            "policy": agent.policy_net.state_dict(),
            "target": agent.target_net.state_dict(),
            "optimizer": agent.optimizer.state_dict(),
            "epsilon": agent.epsilon,
            "shot_history": shot_history,
            "loss_history": loss_history,
        },
        path,
    )

def load_checkpoint(path, agent):
    ckpt = torch.load(path, map_location=agent.device, weights_only=False)
    agent.policy_net.load_state_dict(ckpt["policy"])
    agent.target_net.load_state_dict(ckpt["target"])
    agent.optimizer.load_state_dict(ckpt["optimizer"])
    agent.epsilon = ckpt["epsilon"]
    return ckpt["episode"], ckpt["shot_history"], ckpt["loss_history"]

# Zwraca liczbe strzalow i srednia strat na jeden epizod
def run_episode(env, agent, buffer):
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

        loss = train_step(agent, buffer, BATCH_SIZE)
        if loss is not None:
            ep_loss.append(loss)

    avg_loss = sum(ep_loss) / len(ep_loss) if ep_loss else None
    return env.total_shots, avg_loss


# Podsumowanie
def report(ep, shot_history, loss_history, bar_basic, prev_mean):
    window = shot_history[-REPORT_EVERY:]
    mean = sum(window) / len(window)

    losses = [x for x in loss_history[-REPORT_EVERY:] if x is not None]
    loss_txt = f"{sum(losses) / len(losses):.4f}" if losses else "brak"

    trend = "" if prev_mean is None else f" | zmiana {mean - prev_mean:+.1f}"

    tqdm.write(
        f"ep {ep:>5} | srednia {mean:>5.1f} | min {min(window):>3} | max {max(window):>3}"
        f" | do basic_ai {mean - bar_basic:+.1f} | loss {loss_txt}{trend}"
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
    for _ in tqdm(range(EVAL_GAMES), desc="DQN eval", leave=False):
        state, _ = env.reset()
        done = False
        while not done:
            mask = env.get_valid_actions()
            action = agent.select_action(state, mask)
            state, _, terminated, truncated, _ = env.step(action)
            done = terminated or truncated
        shots.append(env.total_shots)

    agent.epsilon = old_eps

    print("\n" + "=" * 46)
    print(f"{'Agent':<12} | {'Srednia':>8} | {'Min':>5} | {'Max':>5}")
    print("-" * 46)
    print(f"{'DQN':<12} | {np.mean(shots):>8.1f} | {min(shots):>5} | {max(shots):>5}")
    print(f"{'basic_ai':<12} | {bar_basic:>8.1f} | {'':>5} | {'':>5}")
    print(f"{'random':<12} | {bar_random:>8.1f} | {'':>5} | {'':>5}")
    print("=" * 46)


def main():
    env = BattleshipEnv()
    agent = DQNAgent(
        epsilon=EPSILON_START,
        epsilon_min=EPSILON_MIN,
        epsilon_decay=epsilon_decay_for(NUM_EPISODES),
    )
    buffer = ReplayBuffer()

    print(f"Urzadzenie : {agent.device}")
    print(f"Epizody    : {NUM_EPISODES}")
    print(f"Epsilon    : {EPSILON_START} do {EPSILON_MIN} przez "
          f"{int(DECAY_SPAN * NUM_EPISODES)} epizodow")
    print()

    # Start od nowa
    start_ep = 1
    shot_history, loss_history = [], []
    if os.path.exists(CHECKPOINT_PATH):
        last_ep, shot_history, loss_history = load_checkpoint(CHECKPOINT_PATH, agent)
        start_ep = last_ep + 1
        print(f"Checkpoint : wznowienie od epizodu {start_ep}, epsilon {agent.epsilon:.3f}")
        print("Bufor startuje pusty, wiec pierwsze epizody po wznowieniu nie ucza")
        print()

    # Bramka do poprawienia wydjanosci (by nie liczylo 4h)
    if start_ep > NUM_EPISODES:
        print("Przebieg juz skonczony. Skasuj checkpoint, zeby zaczac od nowa.")
        return

    print("Liczenie poprzeczki...")
    bar_random = baseline(BASELINE_GAMES, "random")
    bar_basic = baseline(BASELINE_GAMES, "basic_ai")
    print(f"random   : {bar_random:.1f} strzalow")
    print(f"basic_ai : {bar_basic:.1f} strzalow")
    print()

    prev_mean = None
    pbar = tqdm(range(start_ep, NUM_EPISODES + 1), desc="DQN", unit="ep",
                initial=start_ep - 1, total=NUM_EPISODES)

    for ep in pbar:
        shots, avg_loss = run_episode(env, agent, buffer)

        shot_history.append(shots)
        loss_history.append(avg_loss)
        agent.decay_epsilon()

        if ep % TARGET_UPDATE == 0:
            agent.update_target()

        # Progress bar
        window = shot_history[-WINDOW:]
        pbar.set_postfix(
            srednia=f"{sum(window) / len(window):.1f}",
            eps=f"{agent.epsilon:.3f}",
            loss="brak" if avg_loss is None else f"{avg_loss:.3f}",
            bufor=len(buffer),
        )

        if ep % REPORT_EVERY == 0:
            prev_mean = report(ep, shot_history, loss_history, bar_basic, prev_mean)

        if ep % SAVE_EVERY == 0:
            agent.save(MODEL_PATH)
            save_checkpoint(CHECKPOINT_PATH, agent, ep, shot_history, loss_history)

    pbar.close()

    agent.save(MODEL_PATH)
    save_checkpoint(CHECKPOINT_PATH, agent, NUM_EPISODES, shot_history, loss_history)
    print(f"\nTrening skonczony. Model: {MODEL_PATH}")

    plot(shot_history, loss_history, bar_random, bar_basic)
    quick_eval(agent, bar_random, bar_basic)


if __name__ == "__main__":
    main()
