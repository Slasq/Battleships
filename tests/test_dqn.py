import os

import pytest
import torch
import torch.nn as nn

from ml.dqn.agent import DQNAgent
from ml.dqn.model import DQN
from ml.dqn.trainer import ReplayBuffer, train_step
from ml.environment import NUM_CHANNELS


@pytest.fixture
def agent():
    torch.manual_seed(0)
    return DQNAgent()


# Sztuczne przejscie do bufora
def fake_transition(terminated=0.0, empty_mask=False):
    state = torch.rand(NUM_CHANNELS, 10, 10)
    next_state = torch.rand(NUM_CHANNELS, 10, 10)
    mask = torch.zeros(100) if empty_mask else torch.ones(100)
    return state, 5, 1.0, next_state, terminated, mask


def test_model_returns_one_q_per_cell():
    out = DQN()(torch.rand(8, NUM_CHANNELS, 10, 10))
    assert out.shape == (8, 100)


def test_model_works_on_smaller_board():
    # Siec bez warstw gestych nie jest zwiazana z rozmiarem planszy
    out = DQN()(torch.rand(2, NUM_CHANNELS, 5, 5))
    assert out.shape == (2, 25)


def test_model_has_no_dense_layers():
    assert not any(isinstance(m, nn.Linear) for m in DQN().modules())


def test_exploration_respects_the_mask(agent):
    agent.epsilon = 1.0
    allowed = {3, 17, 42}
    mask = torch.zeros(100)
    for i in allowed:
        mask[i] = 1.0

    state = torch.rand(NUM_CHANNELS, 10, 10)
    for _ in range(50):
        assert agent.select_action(state, mask) in allowed


def test_exploitation_respects_the_mask(agent):
    agent.epsilon = 0.0
    allowed = {3, 17, 42}
    mask = torch.zeros(100)
    for i in allowed:
        mask[i] = 1.0

    state = torch.rand(NUM_CHANNELS, 10, 10)
    for _ in range(10):
        assert agent.select_action(state, mask) in allowed


def test_select_action_does_not_touch_the_mask(agent):
    mask = torch.ones(100)
    mask[7] = 0.0
    before = mask.clone()

    agent.select_action(torch.rand(NUM_CHANNELS, 10, 10), mask)

    assert torch.equal(mask, before)


def test_epsilon_stops_at_the_floor(agent):
    agent.epsilon = 0.02
    agent.epsilon_min = 0.01

    for _ in range(500):
        agent.decay_epsilon()

    assert agent.epsilon == agent.epsilon_min


def test_update_target_copies_weights(agent):
    agent.policy_net.net[0].weight.data.add_(1.0)
    assert not torch.equal(
        agent.policy_net.net[0].weight, agent.target_net.net[0].weight
    )

    agent.update_target()

    assert torch.equal(agent.policy_net.net[0].weight, agent.target_net.net[0].weight)


def test_save_and_load_roundtrip(agent, tmp_path):
    path = os.path.join(tmp_path, "dqn.pth")
    agent.save(path)

    before = agent.policy_net.net[0].weight.clone()
    agent.policy_net.net[0].weight.data.zero_()
    agent.load(path)

    assert torch.equal(agent.policy_net.net[0].weight, before)

    # Load rowna tez siec celu
    assert torch.equal(agent.policy_net.net[0].weight, agent.target_net.net[0].weight)


def test_buffer_drops_the_oldest():
    buffer = ReplayBuffer(capacity=10)
    for _ in range(25):
        buffer.push(*fake_transition())

    assert len(buffer) == 10


def test_buffer_sample_shapes():
    buffer = ReplayBuffer()
    for _ in range(20):
        buffer.push(*fake_transition())

    states, actions, rewards, next_states, terminateds, masks = buffer.sample(8)

    assert states.shape == (8, NUM_CHANNELS, 10, 10)
    assert next_states.shape == (8, NUM_CHANNELS, 10, 10)
    assert masks.shape == (8, 100)
    assert actions.dtype == torch.long
    assert rewards.dtype == torch.float32
    assert terminateds.dtype == torch.float32


def test_train_step_waits_for_a_full_batch(agent):
    buffer = ReplayBuffer()
    for _ in range(4):
        buffer.push(*fake_transition())

    assert train_step(agent, buffer, batch_size=8) is None


def test_train_step_moves_the_weights(agent):
    buffer = ReplayBuffer()
    for _ in range(16):
        buffer.push(*fake_transition())

    before = agent.policy_net.net[0].weight.clone()
    loss = train_step(agent, buffer, batch_size=8)

    assert loss is not None
    assert torch.isfinite(torch.tensor(loss))
    assert not torch.equal(agent.policy_net.net[0].weight, before)


def test_empty_mask_in_terminal_state_keeps_loss_finite(agent):
    buffer = ReplayBuffer()

    # Plansza ostrzelana do konca zaden ruch nie jest juz dozwolony
    for _ in range(16):
        buffer.push(*fake_transition(terminated=1.0, empty_mask=True))

    loss = train_step(agent, buffer, batch_size=8)

    assert loss is not None
    assert torch.isfinite(torch.tensor(loss))

    grads = [p.grad for p in agent.policy_net.parameters() if p.grad is not None]
    assert all(torch.isfinite(g).all() for g in grads)


def test_empty_mask_without_terminated_keeps_loss_finite(agent):
    buffer = ReplayBuffer()

    # Ucieta partia, plansza pusta, ale flota nie zatopiona
    for _ in range(16):
        buffer.push(*fake_transition(terminated=0.0, empty_mask=True))

    loss = train_step(agent, buffer, batch_size=8)

    assert loss is not None
    assert torch.isfinite(torch.tensor(loss))


def test_terminated_stops_the_bootstrap(agent):
    buffer = ReplayBuffer()

    # Zatopiona flota, wiec target to sama nagroda
    for _ in range(16):
        buffer.push(*fake_transition(terminated=1.0))

    loss = train_step(agent, buffer, batch_size=8)

    assert loss is not None
    assert torch.isfinite(torch.tensor(loss))
