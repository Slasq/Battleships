import pygame
from engine import player, Game

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

INDENT = 10

# Ekran
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))

# Kolor
GREY = (40, 50, 60)
WHITE = (255, 250, 250)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
UNKNOWN_GREY = (129, 133, 137)
COLORS = {"U": UNKNOWN_GREY, "H": RED, "M": BLUE}

# Rysowanie grida
def draw_grid(player, left = 0, top = 0, search = False):
    for i in range(100):
        x = left + i % 10 * GRID_SIZE
        y = top + i // 10 * GRID_SIZE
        square = pygame.Rect(x, y, GRID_SIZE, GRID_SIZE)
        pygame.draw.rect(SCREEN, WHITE, square, width = 3)
        if search:
            x += GRID_SIZE // 2
            y += GRID_SIZE // 2
            pygame.draw.circle(SCREEN, COLORS[player.search[i]], (x, y), radius=GRID_SIZE // 4)

# Dodawanie statkow na plansze
def draw_ships(player, left = 0, top = 0):
    for ship in player.ships:
        x = left + ship.col * GRID_SIZE + INDENT
        y = top + ship.row * GRID_SIZE + INDENT
        if ship.orientation == "h":
            WIDTH = ship.size * GRID_SIZE - 2 * INDENT
            HEIGHT = GRID_SIZE - 2 * INDENT
        else:
            WIDTH = GRID_SIZE - 2 * INDENT
            HEIGHT = ship.size * GRID_SIZE - 2 * INDENT
        rectangle = pygame.Rect(x, y, WIDTH, HEIGHT)
        pygame.draw.rect(SCREEN, GREEN, rectangle, border_radius = 12)

game = Game()

# Interakcje
animation = True
pauza = False

while animation:

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            animation = False

        if event.type == pygame.MOUSEBUTTONDOWN:
            x, y = pygame.mouse.get_pos()
            if game.player1_turn and x < GRID_SIZE * 10 and y < 10 * GRID_SIZE:
                row = y // GRID_SIZE
                col = x // GRID_SIZE
                index = row * 10 + col
                game.move(index)


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
        draw_grid(game.player1, search = True)
        draw_grid(game.player2, search = True ,left = (WIDTH - HORIZON)//2 + HORIZON)

        # Positioning grid
        draw_grid(game.player1, top = (HEIGHT - VERTICAL)//2 + VERTICAL)
        draw_grid(game.player2, left = (WIDTH - HORIZON)//2 + HORIZON, top = (HEIGHT - VERTICAL)//2 + VERTICAL)

        # Nanoszenie statkow graczy
        draw_ships(game.player1, top = (HEIGHT - VERTICAL)//2 + VERTICAL)
        draw_ships(game.player2, left = (WIDTH - HORIZON)//2 + HORIZON)

        pygame.display.flip()
