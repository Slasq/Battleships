import pytest

from engine import Game, Ship, player

# Flota z player.place_ships
FLEET_SIZES = [5, 4, 3, 3, 2]
FLEET_CELLS = sum(FLEET_SIZES)


@pytest.fixture
def game():
    return Game(human1=False, human2=False)


def test_ship_stays_in_one_row_or_column():
    for _ in range(200):
        ship = Ship(size=4)
        indexes = ship.indexes

        assert len(indexes) == ship.size
        assert all(0 <= i < 100 for i in indexes)

        rows = {i // 10 for i in indexes}
        cols = {i % 10 for i in indexes}

        # Poziomy statek trzyma jeden wiersz, pionowy jedna kolumne
        if ship.orientation == "h":
            assert len(rows) == 1
        else:
            assert len(cols) == 1


def test_fleet_has_right_sizes_and_no_overlap():
    for _ in range(50):
        p = player()

        assert sorted(s.size for s in p.ships) == sorted(FLEET_SIZES)

        # Statki moga sie stykac, ale nie nachodzic
        assert len(p.indexes) == FLEET_CELLS
        assert len(set(p.indexes)) == FLEET_CELLS


def test_fresh_board_is_all_unknown(game):
    assert game.player1.search == ["U"] * 100
    assert game.player2.search == ["U"] * 100
    assert game.over is False
    assert game.player1_turn is True


def test_hit_marks_h_and_keeps_turn(game):
    target = game.player2.indexes[0]
    game.move(target)

    assert game.player1.search[target] == "H"

    # Trafienie nie oddaje tury
    assert game.player1_turn is True


def test_miss_marks_m_and_passes_turn(game):
    empty = next(i for i in range(100) if i not in game.player2.indexes)
    game.move(empty)

    assert game.player1.search[empty] == "M"
    assert game.player1_turn is False


def test_sunk_ship_turns_to_s(game):
    ship = min(game.player2.ships, key=lambda s: s.size)

    for i in ship.indexes[:-1]:
        game.player1_turn = True
        game.move(i)

    # Przed ostatnim polem statek nie jest zatopiony
    assert all(game.player1.search[i] == "H" for i in ship.indexes[:-1])

    game.player1_turn = True
    game.move(ship.indexes[-1])

    assert all(game.player1.search[i] == "S" for i in ship.indexes)


def test_game_ends_after_whole_fleet(game):
    targets = list(game.player2.indexes)

    for i in targets[:-1]:
        game.player1_turn = True
        game.move(i)
        assert game.over is False

    game.player1_turn = True
    game.move(targets[-1])

    assert game.over is True


def test_second_player_uses_own_search(game):
    game.player1_turn = False
    target = game.player1.indexes[0]
    game.move(target)

    assert game.player2.search[target] == "H"
    assert game.player1.search[target] == "U"
