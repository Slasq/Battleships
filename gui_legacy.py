import pygame
from engine import FLEET, Game, Ship, fits
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
COLORS = {"U": UNKNOWN_GREY, "H": RED, "M": BLUE, "S": BLACK}

# Podglad roztawienia statkow
PREVIEW_OK = (60, 220, 90)
PREVIEW_BAD = (220, 70, 70)

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

# Rozstawienie floty wroga Q, W, E
PLACER_KEYS = [
    (pygame.K_q, pol.UNIFORM),
    (pygame.K_w, pol.HUMAN),
    (pygame.K_e, pol.HIDE),
]

placer_name = pol.UNIFORM

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

# Prostokat statku w kratkach planszy
def ship_rect(row, col, size, orientation, left = 0, top = 0):
    x = left + col * GRID_SIZE + INDENT
    y = top + row * GRID_SIZE + INDENT
    if orientation == "h":
        w = size * GRID_SIZE - 2 * INDENT
        h = GRID_SIZE - 2 * INDENT
    else:
        w = GRID_SIZE - 2 * INDENT
        h = size * GRID_SIZE - 2 * INDENT
    return pygame.Rect(x, y, w, h)


# Dodawanie statkow na plansze
def draw_ships(player, left = 0, top = 0):
    for ship in player.ships:
        rectangle = ship_rect(ship.row, ship.col, ship.size, ship.orientation, left, top)
        pygame.draw.rect(SCREEN, GREEN, rectangle, border_radius = 12)


# Kratka pod kursorem na planszy o zadanym poczatku
def cell_at(pos, left = 0, top = 0):
    x, y = pos
    if not (left <= x < left + GRID_SIZE * 10 and top <= y < top + GRID_SIZE * 10):
        return None
    return ((y - top) // GRID_SIZE) * 10 + (x - left) // GRID_SIZE


# Flota przeciwnika z wybranej polityki rozstawienia
def new_game():
    return Game(HUMAN1, HUMAN2, ships1 = [], ships2 = pol.placer(placer_name)())


game = new_game()
next_ai = 0

# Faza gry roztawienie next walka
phase = "place"
orientation = "h"


def placing_done():
    return len(game.player1.ships) >= len(FLEET)


def next_size():
    return FLEET[len(game.player1.ships)]


# Interakcje
animation = True
pauza = False

while animation:

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            animation = False

        if event.type == pygame.MOUSEBUTTONDOWN and not game.over:
            pos = pygame.mouse.get_pos()

            # Stawianie floty na wlasnej planszy
            if phase == "place":
                index = cell_at(pos, top = TOP_INDENT)
                if index is not None:
                    ship = Ship(next_size(), row = index // 10, col = index % 10,
                                orientation = orientation)
                    if game.player1.add_ship(ship) and placing_done():
                        phase = "battle"

            # Strzelanie po planszy przeciwnika
            elif game.player1_turn:
                index = cell_at(pos)
                if index is not None and game.player1.search[index] == "U":
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
                game = new_game()
                next_ai = 0
                phase = "place"

            if phase == "place":
                # Obrot stawianego statku
                if event.key == pygame.K_r:
                    orientation = "v" if orientation == "h" else "h"

                # Cofniecie ostatniego statku
                if event.key == pygame.K_BACKSPACE:
                    game.player1.remove_last_ship()

                # Dolosowanie reszty floty
                if event.key == pygame.K_l:
                    game.player1.place_ships(FLEET[len(game.player1.ships):])
                    phase = "battle"

            # Zmiana modelu w trakcie
            for key, name in MODEL_KEYS:
                if event.key == key:
                    ai_name = name
                    ai_move = pol.get(name)

            # Zmiana rozstawienia wroga od nastepnej tury
            for key, name in PLACER_KEYS:
                if event.key == key:
                    placer_name = name

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
        if phase == "battle":
            draw_ships(game.player2, left = LEFT_INDENT)

        # Podglad statku pod kursorem
        if phase == "place":
            index = cell_at(pygame.mouse.get_pos(), top = TOP_INDENT)
            if index is not None:
                row, col = index // 10, index % 10
                ship = Ship(next_size(), row = row, col = col, orientation = orientation)
                color = PREVIEW_OK if fits(ship, set(game.player1.indexes)) else PREVIEW_BAD
                pygame.draw.rect(SCREEN, color,
                                 ship_rect(row, col, ship.size, orientation, top = TOP_INDENT),
                                 width = 4, border_radius = 12)

        # Ruch przeciwnika
        if phase == "battle" and not game.over and game.computer_turn:
            if pygame.time.get_ticks() >= next_ai:
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
        if phase == "place":
            hud = (f"stawiasz statek {len(game.player1.ships) + 1}/{len(FLEET)}"
                   f" o dlugosci {next_size()}   [R] obrot  [BACKSPACE] cofnij  [L] losowo")
        else:
            shots = sum(1 for s in game.player1.search if s != "U")
            tura = "twoj ruch" if game.player1_turn else "ruch przeciwnika"
            hud = (f"model: {ai_name} [1-5]   flota AI: {placer_name} [Q/W/E]"
                   f"   {tura}   twoje strzaly: {shots}")

        SCREEN.blit(small_font.render(hud, True, WHITE, GREY), (4, GRID_SIZE * 10 + 4))

        pygame.display.flip()
