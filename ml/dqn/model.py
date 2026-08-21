import torch.nn as nn

from ..environment import NUM_CHANNELS


class DQN(nn.Module):
    def __init__(self, in_channels=NUM_CHANNELS, width=64, depth=3):
        super().__init__()
        layers = []
        channels = in_channels

        # Conv 3x3 z ReLU
        for _ in range(depth):
            layers.append(nn.Conv2d(channels, width, kernel_size=3, padding=1))
            layers.append(nn.ReLU())
            channels = width

        self.trunk = nn.Sequential(*layers)

        # Jedna wartosc Q na pole
        self.advantage = nn.Conv2d(width, 1, kernel_size=1)

        # Jedna wartosc na cala plansze
        self.value = nn.Sequential(
            nn.Conv2d(width, width, kernel_size=1),
            nn.ReLU(),
            nn.Conv2d(width, 1, kernel_size=1),
        )

    def forward(self, x):
        feat = self.trunk(x)

        # Flatten do wektora akcji
        adv = self.advantage(feat).flatten(start_dim=1)

        # Srednia przewagi zbija do zera
        adv = adv - adv.mean(dim=1, keepdim=True)

        # Usrednienie do planszy
        val = self.value(feat).mean(dim=(2, 3))

        return val + adv
