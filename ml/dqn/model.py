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

        # Jedna wartosc Q na pole
        layers.append(nn.Conv2d(width, 1, kernel_size=1))
        self.net = nn.Sequential(*layers)

    def forward(self, x):
        # Flatten do wektora akcji
        return self.net(x).flatten(start_dim=1)
