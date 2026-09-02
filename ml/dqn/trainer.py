import random
from collections import deque

import torch
import torch.nn.functional as F


class ReplayBuffer:
    def __init__(self, capacity=50_000):

        # Najstarsze przejscia
        self.buffer = deque(maxlen=capacity)

    # Zapis jednego przejscia
    def push(self, state, action, reward, next_state, terminated, valid_mask):
        self.buffer.append((state, action, reward, next_state, terminated, valid_mask))

    # Losowa partia do treningu
    def sample(self, batch_size):
        batch = random.sample(self.buffer, batch_size)
        states, actions, rewards, next_states, terminateds, masks = zip(*batch)

        # Krotki na tensory
        return (
            torch.stack(states),
            torch.tensor(actions, dtype=torch.long),
            torch.tensor(rewards, dtype=torch.float32),
            torch.stack(next_states),
            torch.tensor(terminateds, dtype=torch.float32),
            torch.stack(masks),
        )

    def __len__(self):
        return len(self.buffer)


def train_step(agent, replay_buffer, batch_size=512):

    # Za malo danych na pelna partie
    if len(replay_buffer) < batch_size:
        return None

    batch = replay_buffer.sample(batch_size)
    states, actions, rewards, next_states, terminateds, masks = batch

    # Partia z bufora na sieci
    device = agent.device
    states = states.to(device)
    actions = actions.to(device)
    rewards = rewards.to(device)
    next_states = next_states.to(device)
    terminateds = terminateds.to(device)
    masks = masks.to(device)

    # Q dla wykonanej akcji
    q_values = agent.policy_net(states).gather(1, actions.unsqueeze(1)).squeeze(1)

    with torch.no_grad():
        # Double DQN akcje wybiera siec uczaca
        next_online = agent.policy_net(next_states)

        # Pola sprawdzona nie sa sprawdzane ponownie
        next_online[masks == 0] = -float("inf")
        best_actions = next_online.argmax(dim=1, keepdim=True)

        # Wycene wybranej akcji daje siec celu
        next_q = agent.target_net(next_states)
        max_next_q = next_q.gather(1, best_actions).squeeze(1)

        # Zapelniona plansza = koniec gry
        max_next_q[masks.sum(dim=1) == 0] = 0.0

        # Zabicie wszystki statkow = koniec gry
        max_next_q[terminateds == 1] = 0.0

        target = rewards + agent.gamma * max_next_q

    loss = F.smooth_l1_loss(q_values, target)
    agent.optimizer.zero_grad()
    loss.backward()

    # Ciecie gradientu
    torch.nn.utils.clip_grad_norm_(agent.policy_net.parameters(), 10.0)
    agent.optimizer.step()

    # Licznik pilnuje kopiowania wag do sieci celu
    agent.count_learn_step()

    return loss.item()
