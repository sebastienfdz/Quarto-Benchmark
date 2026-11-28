import logging

import pytest

from quarto_benchmark.game.piece import Piece, generate_all_pieces
from quarto_benchmark.game.state import GameState
from quarto_benchmark.game.types import GameResult
from quarto_benchmark.players.base import BaseModel
from quarto_benchmark.runners.game_runner import GameRunner


class StubPlayer(BaseModel):
    """Deterministic player returning pre-scripted positions and pieces."""

    def __init__(
        self,
        name: str,
        positions: list[tuple[int, int]],
        pieces: list[Piece],
    ) -> None:
        super().__init__(name)
        self._positions = iter(positions)
        self._pieces = iter(pieces)

    def choose_position(self, state: GameState, piece: Piece) -> tuple[int, int]:
        return next(self._positions)

    def choose_piece(self, state: GameState) -> Piece:
        return next(self._pieces)


def test_game_runner_player_1_wins(caplog: pytest.LogCaptureFixture) -> None:
    """Player 1 wins when completing row 0 on the 4th placement."""
    pieces = generate_all_pieces()
    p1 = StubPlayer("Alice", positions=[(0, 1), (0, 3)], pieces=[pieces[0], pieces[2]])
    p2 = StubPlayer("Bob", positions=[(0, 0), (0, 2)], pieces=[pieces[1], pieces[3]])

    runner = GameRunner(p1, p2)
    with caplog.at_level(logging.INFO, logger="quarto_benchmark.game_runner"):
        runner.run()

    assert runner.game.result == GameResult.PLAYER_1
    assert "Player 1: Alice" in caplog.text
    assert "Player 2: Bob" in caplog.text
    assert "Player 1 (Alice) wins!" in caplog.text


def test_game_runner_player_2_wins(caplog: pytest.LogCaptureFixture) -> None:
    """Player 2 wins when completing row 0 on the 5th placement."""
    pieces = generate_all_pieces()
    p1 = StubPlayer(
        "Alice",
        positions=[(0, 1), (1, 1)],
        pieces=[pieces[0], pieces[2], pieces[4]],
    )
    p2 = StubPlayer(
        "Bob",
        positions=[(0, 0), (0, 2), (0, 3)],
        pieces=[pieces[1], pieces[3]],
    )

    runner = GameRunner(p1, p2)
    with caplog.at_level(logging.INFO, logger="quarto_benchmark.game_runner"):
        runner.run()

    assert runner.game.result == GameResult.PLAYER_2
    assert "Player 2 (Bob) wins!" in caplog.text


def test_game_runner_draw(caplog: pytest.LogCaptureFixture) -> None:
    """A full board with no Quarto ends in a draw and logs 'Draw.'."""
    pieces = generate_all_pieces()
    draw_grid = [
        [0, 2, 1, 15],
        [5, 4, 3, 12],
        [10, 13, 11, 7],
        [14, 8, 6, 9],
    ]
    steps = [(pieces[draw_grid[x][y]], (x, y)) for x in range(4) for y in range(4)]

    p1 = StubPlayer(
        "Alice",
        positions=[pos for _, pos in steps[1::2]],
        pieces=[piece for piece, _ in steps[0::2]],
    )
    p2 = StubPlayer(
        "Bob",
        positions=[pos for _, pos in steps[0::2]],
        pieces=[piece for piece, _ in steps[1::2]],
    )

    runner = GameRunner(p1, p2)
    with caplog.at_level(logging.INFO, logger="quarto_benchmark.game_runner"):
        runner.run()

    assert runner.game.result == GameResult.DRAW
    assert "Draw." in caplog.text


def test_play_turn_without_next_piece_raises() -> None:
    """Calling _play_turn when no piece has been selected must raise ValueError."""
    runner = GameRunner(StubPlayer("P1", [], []), StubPlayer("P2", [], []))
    with pytest.raises(ValueError, match="No piece selected"):
        runner._play_turn()
