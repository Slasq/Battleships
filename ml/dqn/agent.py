import random
import torch
from .model import DQN

class DQNAgent:
    def __init__(self, lr=1e-4, gamma=0.99, epsilon=1.0, epsilon_min=0.01,
                 epsilon_decay=0.995, device=None):
        # GPU jesli dostepne
        self.device = device or torch.device("cuda" if torch.cuda.is_available() else "cpu")

        self.gamma = gamma
        self.epsilon = epsilon
        self.epsilon_min = epsilon_min
        self.epsilon_decay = epsilon_decay

        # Siec uczaca i siec celu
        self.policy_net = DQN().to(self.device)
        self.target_net = DQN().to(self.device)

        # Start z tych samych wag
        self.target_net.load_state_dict(self.policy_net.state_dict())
        self.target_net.eval()

        self.optimizer = torch.optim.Adam(self.policy_net.parameters(), lr=lr)

    # Greedy z maska akcji
    def select_action(self, state, valid_mask):
        # Maska na tym samym urzadzeniu co siec
        valid_mask = valid_mask.to(self.device)

        # Losowe pole nietrafione
        if random.random() < self.epsilon:
            valid_indices = torch.nonzero(valid_mask).squeeze(-1).tolist()
            return random.choice(valid_indices)

        # Najwyzsze Q wsrod legalnych pul
        with torch.no_grad():
            q = self.policy_net(state.unsqueeze(0).to(self.device)).squeeze(0)
            q[valid_mask == 0] = -float("inf")
            return q.argmax().item()

    # Wygaszanie poszukiwan
    def decay_epsilon(self):
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)

    # Kopiowanie wag do sieci
    def update_target(self):
        self.target_net.load_state_dict(self.policy_net.state_dict())

    def save(self, path):
        torch.save(self.policy_net.state_dict(), path)

    def load(self, path):
        self.policy_net.load_state_dict(torch.load(path, map_location=self.device))
        self.target_net.load_state_dict(self.policy_net.state_dict())
