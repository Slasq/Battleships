import random

import pytest

from engine import Game
from ml.probmap.solver import (
    DEFAULT_FLEET,
    best_move,
    placements,
    probability_map,
    remaining_sizes,
)


@pytest.fixture
def empty_search():
    return ["U"] * 100


def test_placements_count():
    # Dla dlugosci 5: 10 wierszy * 6 pozycji, razy dwie orientacje
    assert len(placements(5)) == 120
    assert len(placements(2)) == 180

    # Zadne rozstawienie nie wychodzi poza plansze ani nie zawija wiersza
    for size in DEFAULT_FLEET:
        for placement in placements(size):
            rows = {i // 10 for i in placement}
            cols = {i % 10 for i in placement}
            assert len(rows) == 1 or len(cols) == 1
            assert all(0 <= i < 100 for i in placement)


def test_map_sums_to_one(empty_search):
    probs = probability_map(empty_search)
    assert sum(probs) == pytest.approx(1.0)


def test_center_beats_corner_on_empty_board(empty_search):
    probs = probability_map(empty_search)

    # Przez srodek przechodzi wiecej rozstawien niz przez rog
    assert probs[44] > probs[0]
    assert probs[44] == max(probs)


def test_missed_cell_has_zero_and_blocks_neighbours(empty_search):
    search = list(empty_search)
    search[44] = "M"

    probs = probability_map(search)
    assert probs[44] == 0.0

    # Pudlo w srodku obniza pola, przez ktore szly rozstawienia przez nie
    assert probs[45] < probability_map(empty_search)[45]


def test_hit_pulls_mass_to_neighbours(empty_search):
    search = list(empty_search)
    search[44] = "H"

    probs = probability_map(search)
    neighbours = [34, 54, 43, 45]

    # Cala masa siedzi wokol trafienia
    assert best_move(search) in neighbours
    for i, p in enumerate(probs):
        if i not in neighbours:
            assert p < min(probs[n] for n in neighbours)


def test_two_hits_in_line_continue_the_line(empty_search):
    search = list(empty_search)
    search[44] = "H"
    search[45] = "H"

    # Konce linii bija pola z boku, bo pokrywaja dwa trafienia naraz
    assert best_move(search) in (43, 46)


def test_remaining_sizes_after_a_sunk_ship(empty_search):
    search = list(empty_search)
    for i in (40, 41, 42, 43, 44):
        search[i] = "S"

    assert sorted(remaining_sizes(search)) == [2, 3, 3, 4]


def test_remaining_sizes_with_two_touching_ships(empty_search):
    search = list(empty_search)

    # Piatka i dwojka stykaja sie w jednym wierszu
    for i in (40, 41, 42, 43, 44):
        search[i] = "S"
    for i in (45, 46):
        search[i] = "S"

    assert sorted(remaining_sizes(search)) == [3, 3, 4]


def test_remaining_sizes_falls_back_on_impossible_board(empty_search):
    search = list(empty_search)

    # Trzy pola w rogu, ktorych nie da sie zlozyc z zadnej floty
    search[0] = "S"
    search[1] = "S"
    search[11] = "S"

    assert sorted(remaining_sizes(search)) == sorted(DEFAULT_FLEET)


def test_sunk_ship_does_not_attract_shots(empty_search):
    search = list(empty_search)
    for i in (40, 41, 42, 43, 44):
        search[i] = "S"

    probs = probability_map(search)

    # Zatopiony statek jest domkniety, wiec nie ciagnie do siebie strzalow
    assert all(probs[i] == 0.0 for i in (40, 41, 42, 43, 44))
    assert sum(probs) == pytest.approx(1.0)


def test_best_move_returns_none_on_full_board():
    assert best_move(["M"] * 100) is None


def test_best_move_never_repeats_a_cell(empty_search):
    search = list(empty_search)
    rng = random.Random(0)

    for _ in range(100):
        move = best_move(search, rng=rng)
        assert move is not None
        assert search[move] == "U"
        search[move] = "M"

    assert best_move(search, rng=rng) is None


def test_solver_finishes_a_real_game():
    game = Game(human1=False, human2=False)
    shots = 0

    while not game.over:
        game.player1_turn = True
        move = best_move(game.player1.search)
        assert move is not None
        game.move(move)
        game.player1_turn = True
        shots += 1
        assert shots <= 100

    assert game.over is True
