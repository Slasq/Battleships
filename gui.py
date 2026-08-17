import pygame
from engine import player

pygame.init()
pygame.display.set_caption("Statki")

# Grid
# Uklad liczony w kratkach
COLS = 1 + 10 + 2 + 10 + 1
ROWS = 1 + 10 + 1 + 10 + 1

# Kratka dostosowywanie do rozdzielczosci ekranu
DESKTOP_W, DESKTOP_H = pygame.display.get_desktop_sizes()[0]
GRID_SIZE = min(int(DESKTOP_W * 0.9) // COLS, int(DESKTOP_H * 0.85) // ROWS)

HORIZON = GRID_SIZE
VERTICAL = GRID_SIZE

WIDTH = GRID_SIZE * COLS
HEIGHT = GRID_SIZE * ROWS

# Ekran
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))

# Kolor
GREY = (40, 50, 60)
WHITE = (255, 250, 250)
GREEN = (0, 255, 0)

# Rysowanie grida
def draw_grid(left = 0, top = 0):
    for i in range(100):
        x = left + i % 10 * GRID_SIZE
        y = top + i // 10 * GRID_SIZE
        square = pygame.Rect(x, y, GRID_SIZE, GRID_SIZE)
        pygame.draw.rect(SCREEN, WHITE, square, width = 3)

# Dodawanie statkow na plansze
def draw_ships(player, left = 0, top = 0):
    for ship in player.ships:
        x = left + ship.col * GRID_SIZE
        y = top + ship.row * GRID_SIZE
        if ship.orientation == "h":
            WIDTH = ship.size * GRID_SIZE
            HEIGHT = GRID_SIZE
        else:
            WIDTH = GRID_SIZE
            HEIGHT = ship.size * GRID_SIZE
        rectangle = pygame.Rect(x, y, WIDTH, HEIGHT)
        pygame.draw.rect(SCREEN, GREEN, rectangle)



player = player()
# Interakcje
animation = True
pauza = False

while animation:

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            animation = False

        if event.type == pygame.KEYDOWN:
            # Wylaczenie
            if event.key == pygame.K_ESCAPE:
                animation = False
            # Pauza
            if event.key == pygame.K_SPACE:
                pauza = not pauza

        # Wywolanie
    if not pauza:
        SCREEN.fill(GREY)

        # Serach grid
        draw_grid()
        draw_grid(left = (WIDTH - HORIZON)//2 + HORIZON)

        # Positioning grid
        draw_grid(top = (HEIGHT - VERTICAL)//2 + VERTICAL)
        draw_grid(left = (WIDTH - HORIZON)//2 + HORIZON, top = (HEIGHT - VERTICAL)//2 + VERTICAL)

        # Nanoszenie statkow
        draw_ships(player)

        pygame.display.flip()
