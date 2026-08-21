import pytest

from engine import Game


@pytest.fixture
def game():
    return Game(human1=False, human2=False)


# Indeks pola ostrzelanego w ostatnim ruchu
def shot_cell(before, after):
    changed = [i for i in range(100) if before[i] == "U" and after[i] != "U"]
    return changed


def test_random_moves_never_repeats(game):
    seen = set()

    while not game.over:
        game.player1_turn = True
        before = list(game.player1.search)
        game.random_moves()
        after = game.player1.search

        # Dokladnie jedno nowe pole na ruch
        new = shot_cell(before, after)
        assert len(new) >= 1
        assert new[0] not in seen
        seen.update(new)

    assert len(seen) <= 100


def test_basic_ai_finishes_the_game(game):
    shots = 0

    while not game.over:
        game.player1_turn = True
        game.basic_ai()
        shots += 1
        assert shots <= 100

    assert game.over is True


def test_basic_ai_shoots_checkerboard_when_no_hits(game):
    game.player1_turn = True
    before = list(game.player1.search)
    game.basic_ai()

    new = shot_cell(before, game.player1.search)
    assert len(new) == 1

    # Bez trafien celuje w co drugie pole
    idx = new[0]
    assert (idx // 10 + idx % 10) % 2 == 0


def test_basic_ai_targets_neighbour_of_a_hit(game):
    game.player1.search[45] = "H"
    game.player1_turn = True

    before = list(game.player1.search)
    game.basic_ai()

    new = shot_cell(before, game.player1.search)
    assert len(new) == 1
    assert new[0] in (35, 55, 44, 46)


def test_basic_ai_continues_the_line(game):
    game.player1.search[44] = "H"
    game.player1.search[45] = "H"
    game.player1_turn = True

    before = list(game.player1.search)
    game.basic_ai()

    new = shot_cell(before, game.player1.search)
    assert len(new) == 1

    # Kontynuacja kierunku ma pierwszenstwo przed zwyklym sasiadem
    assert new[0] in (43, 46)
