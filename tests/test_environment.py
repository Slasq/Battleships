import pytest
import torch

from ml.environment import (
    NUM_CHANNELS,
    REWARD_HIT,
    REWARD_MISS,
    REWARD_SUNK,
    REWARD_WIN,
    BattleshipEnv,
)


@pytest.fixture
def env():
    return BattleshipEnv()


# Pole floty przeciwnika
def ship_cell(env, n=0):
    return env.game.player2.indexes[n]


# Pole poza flota przeciwnika
def empty_cell(env):
    return next(i for i in range(100) if i not in env.game.player2.indexes)


def test_board_size_comes_from_engine(env):
    assert env.cells == 100
    assert env.board_size == 10
    assert env.max_steps == 100


def test_reset_returns_state_and_mask(env):
    state, info = env.reset()

    assert state.shape == (NUM_CHANNELS, 10, 10)
    assert "action_mask" in info
    assert info["action_mask"].sum().item() == 100


def test_state_is_one_hot(env):
    env.step(ship_cell(env))
    env.step(empty_cell(env))
    state = env.get_state()

    # Kazde pole nalezy do dokladnie jednego kanalu
    assert torch.all(state.sum(dim=0) == 1.0)
    assert state.dtype == torch.float32


def test_fresh_board_is_all_unknown(env):
    state, _ = env.reset()

    assert state[0].sum().item() == 100
    assert state[1:].sum().item() == 0


def test_mask_drops_the_shot_cell(env):
    target = ship_cell(env)
    _, _, _, _, info = env.step(target)

    mask = info["action_mask"]
    assert mask[target].item() == 0.0
    assert mask.sum().item() == 99


def test_step_returns_five_values(env):
    out = env.step(empty_cell(env))
    assert len(out) == 5


def test_repeated_shot_raises(env):
    target = empty_cell(env)
    env.step(target)

    # Maska akcji jest jedynym zabezpieczeniem, env nie karze cicho
    with pytest.raises(ValueError):
        env.step(target)


def test_miss_and_hit_rewards(env):
    _, reward, _, _, info = env.step(empty_cell(env))
    assert reward == REWARD_MISS
    assert info["event"] == "miss"

    _, reward, _, _, info = env.step(ship_cell(env))
    assert reward == REWARD_HIT
    assert info["event"] == "hit"


def test_sunk_reward(env):
    ship = min(env.game.player2.ships, key=lambda s: s.size)

    for i in ship.indexes[:-1]:
        _, reward, _, _, info = env.step(i)
        assert info["event"] == "hit"

    _, reward, _, _, info = env.step(ship.indexes[-1])
    assert reward == REWARD_SUNK
    assert info["event"] == "sunk"


def test_win_terminates(env):
    targets = list(env.game.player2.indexes)

    for i in targets[:-1]:
        _, _, terminated, truncated, _ = env.step(i)
        assert terminated is False
        assert truncated is False

    _, reward, terminated, truncated, info = env.step(targets[-1])

    assert terminated is True
    assert truncated is False
    assert reward == REWARD_WIN
    assert info["event"] == "win"
    assert env.total_shots == 17


def test_truncation_fires_on_step_limit():
    env = BattleshipEnv(max_steps=5)
    empty = [i for i in range(100) if i not in env.game.player2.indexes]

    for i in empty[:4]:
        _, _, terminated, truncated, _ = env.step(i)
        assert truncated is False

    _, _, terminated, truncated, _ = env.step(empty[4])

    # Wyczerpanie limitu to truncated, nie terminated
    assert truncated is True
    assert terminated is False
