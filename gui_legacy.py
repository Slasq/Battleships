# Old gui for fast testing 

import pygame
from engine import player, Game
from ml import policies as pol

pygame.init()
pygame.display.set_caption("Statki")

# Font
pygame.font.init()
font = pygame.font.SysFont("Arial", 36)
small_font = pygame.font.SysFont("Arial", 20)

# Grid
# Uklad liczony w kratkaaaach
COLS = 1 + 10 + 2 + 10 + 1
ROWS = 1 + 10 + 1 + 10 + 1

# Kratka dostosowywanie do rozdzielczosci ekranu
DESKTOP_W, DESKTOP_H = pygame.display.get_desktop_sizes()[0]
GRID_SIZE = min(int(DESKTOP_W * 0.9) // COLS, int(DESKTOP_H * 0.85) // ROWS)

HORIZON = GRID_SIZE * 2
VERTICAL = GRID_SIZE

LEFT_INDENT = GRID_SIZE * 10 + HORIZON
TOP_INDENT = GRID_SIZE * 10 + VERTICAL

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
BLACK = (0, 0, 0)
COLORS = {"U": UNKNOWN_GREY, "H": RED, "M": BLUE, "S":BLACK}

HUMAN1 = True
HUMAN2 = False

# Wybór modelu 1-5
MODEL_KEYS = [
    (pygame.K_1, pol.RANDOM),
    (pygame.K_2, pol.BASIC),
    (pygame.K_3, pol.PROBMAP),
    (pygame.K_4, pol.PROBMAP_PRIOR),
    (pygame.K_5, pol.DQN),
]

ai_name = pol.PROBMAP
ai_move = pol.get(ai_name)

# Opoxnienie
AI_DELAY = 300

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

game = Game(HUMAN1, HUMAN2)
next_ai = 0

# Interakcje
animation = True
pauza = False

while animation:

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            animation = False

        if event.type == pygame.MOUSEBUTTONDOWN and not game.over:
            x, y = pygame.mouse.get_pos()
            if game.player1_turn and x < GRID_SIZE * 10 and y < GRID_SIZE * 10:
                row = y // GRID_SIZE
                col = x // GRID_SIZE
                index = row * 10 + col
                game.move(index)

            elif HUMAN2 and not game.player1_turn and x >= LEFT_INDENT and x < LEFT_INDENT + GRID_SIZE * 10 and y >= TOP_INDENT and y < TOP_INDENT + GRID_SIZE * 10:
                row = (y - TOP_INDENT) // GRID_SIZE
                col = (x - LEFT_INDENT) // GRID_SIZE
                index = row * 10 + col
                game.move(index)


        if event.type == pygame.KEYDOWN:
            # Wylaczenie
            if event.key == pygame.K_ESCAPE:
                animation = False

            # Pauza
            if event.key == pygame.K_SPACE:
                pauza = not pauza

            # Restart
            if event.key == pygame.K_RETURN:
                game = Game(HUMAN1, HUMAN2)
                next_ai = 0

            # Zmiana modelu w trakcie
            for key, name in MODEL_KEYS:
                if event.key == key:
                    ai_name = name
                    ai_move = pol.get(name)

        # Wywolanie
    if not pauza:
        SCREEN.fill(GREY)

        # Serach grid
        draw_grid(game.player1, search = True)
        draw_grid(game.player2, search = True, left = LEFT_INDENT, top = TOP_INDENT)

        # Positioning grid
        draw_grid(game.player1, top = TOP_INDENT)
        draw_grid(game.player2, left = LEFT_INDENT)

        # Nanoszenie statkow graczy
        draw_ships(game.player1, top = TOP_INDENT)
        draw_ships(game.player2, left = LEFT_INDENT)

        # Ruch przeciwnika
        if not game.over and game.computer_turn and pygame.time.get_ticks() >= next_ai:
            search = game.player1.search if game.player1_turn else game.player2.search
            index = ai_move(search)
            if index is not None:
                game.move(index)
            next_ai = pygame.time.get_ticks() + AI_DELAY

        # Wynik gry
        if game.over:
            text = f"Gracz {game.result} Wins!"
            textbox = font.render(text, False, GREY, WHITE)
            SCREEN.blit(textbox, (WIDTH // 2 - 240, HEIGHT // 2 - 50))

        # Menu stanu
        shots = sum(1 for s in game.player1.search if s != "U")
        tura = "twoj ruch" if game.player1_turn else "ruch przeciwnika"
        hud = f"model: {ai_name}  [1-5]   {tura}   twoje strzaly: {shots}"
        SCREEN.blit(small_font.render(hud, True, WHITE, GREY), (4, GRID_SIZE * 10 + 4))

        pygame.display.flip()
