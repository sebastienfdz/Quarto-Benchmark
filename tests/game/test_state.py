import re

import pytest

from quarto_benchmark.game.exceptions import (
    GameEndedError,
    InvalidPhaseError,
    InvalidPieceError,
    InvalidSquareError,
)
from quarto_benchmark.game.piece import Piece
from quarto_benchmark.game.state import GameState
from quarto_benchmark.game.types import GamePhase, GameResult, Player


@pytest.fixture
def new_game() -> GameState:
    """Create a new game of Quarto."""
    game = GameState()
    assert game.result is None
    assert not game.board.is_full()
    assert not game.board.check_victory()
    assert game.current_player == Player.PLAYER_1
    assert game.phase == GamePhase.SELECTION
    return game


@pytest.fixture
def game_draw() -> GameState:
    """Create a draw game of Quarto."""
    ordered_pieces = [
        [0, 2, 1, 15],
        [5, 4, 3, 12],
        [10, 13, 11, 7],
        [14, 8, 6, 9],
    ]
    game = GameState()
    pieces = game.get_remaining_pieces()

    for x in range(4):
        for y in range(4):
            piece = pieces[ordered_pieces[x][y]]
            game.select_piece(piece)
            game.place_piece(x, y)

    assert game.result == GameResult.DRAW
    assert game.board.is_full()
    assert not game.board.check_victory()
    return game


def test_initial_state(new_game: GameState):
    """At the beginning, Player 1 must select a piece for Player 2."""
    assert new_game.current_player == Player.PLAYER_1
    assert new_game.phase == GamePhase.SELECTION
    assert new_game.next_piece is None


def test_standard_turn_flow(new_game: GameState):
    """Test the state machine transitions (Selection -> Placement -> Selection)."""
    # Action 1: Player 1 selects a piece
    piece = new_game.get_remaining_pieces()[0]
    new_game.select_piece(piece)
    assert new_game.current_player == Player.PLAYER_2
    assert new_game.phase == GamePhase.PLACEMENT
    assert new_game.next_piece == piece

    # Action 2: Player 2 places the piece
    new_game.place_piece(0, 0)
    assert new_game.current_player == Player.PLAYER_2
    assert new_game.phase == GamePhase.SELECTION  # type: ignore[comparison-overlap]

    # Action 3: Player 2 selects the next piece
    piece = new_game.get_remaining_pieces()[0]
    new_game.select_piece(piece)
    assert new_game.current_player == Player.PLAYER_1
    assert new_game.phase == GamePhase.PLACEMENT
    assert new_game.next_piece == piece


def test_game_victory(new_game: GameState):
    """Create a game of Quarto with a winner."""
    pieces = new_game.get_remaining_pieces()
    for i in range(4):
        new_game.select_piece(pieces[i])
        new_game.place_piece(i, 0)

    assert new_game.result in (GameResult.PLAYER_1, GameResult.PLAYER_2)
    assert not new_game.board.is_full()
    assert new_game.board.check_victory()


def test_select_piece_invalid_phase_raises(new_game: GameState):
    """Calling select_piece during PLACEMENT phase should raise InvalidPhaseError."""
    assert new_game.phase == GamePhase.SELECTION
    piece = new_game.get_remaining_pieces()[0]
    new_game.select_piece(piece)
    assert new_game.phase == GamePhase.PLACEMENT  # type: ignore[comparison-overlap]

    with pytest.raises(InvalidPhaseError, match="Invalid phase."):
        new_game.select_piece(new_game.get_remaining_pieces()[0])


def test_place_piece_invalid_phase_raises(new_game: GameState):
    """Calling place_piece during SELECTION phase should raise InvalidPhaseError."""
    assert new_game.phase == GamePhase.SELECTION
    with pytest.raises(InvalidPhaseError, match="Invalid phase."):
        new_game.place_piece(0, 0)


def test_select_piece_game_ended_raises(game_draw: GameState):
    """Playing after the game ended should raise GameEndedError."""
    with pytest.raises(GameEndedError, match="The game is already over."):
        game_draw.select_piece(Piece(0, 0, 0, 0))


def test_place_piece_game_ended_raises(game_draw: GameState):
    """Playing after the game ended should raise GameEndedError."""
    with pytest.raises(GameEndedError, match="The game is already over."):
        game_draw.place_piece(0, 0)


def test_select_piece_invalid_piece_raises(new_game: GameState):
    """Selecting an already used piece should raise InvalidPieceError."""
    piece = new_game.get_remaining_pieces()[0]
    new_game.select_piece(piece)
    new_game.place_piece(0, 0)

    with pytest.raises(InvalidPieceError, match="Piece already played."):
        new_game.select_piece(piece)


def test_place_piece_invalid_square_raises(new_game: GameState):
    """Playing on an occupied square should raise InvalidSquareError."""
    pieces = new_game.get_remaining_pieces()
    new_game.select_piece(pieces[0])
    new_game.place_piece(0, 0)

    new_game.select_piece(pieces[1])
    with pytest.raises(InvalidSquareError, match=r"Square .* not available"):
        new_game.place_piece(0, 0)


def test_play_move_winning(new_game: GameState):
    """
    Playing a winning move should make a victory,
    trying to play again should raise GameEndedError.
    """
    pieces = new_game.get_remaining_pieces()
    for i in range(4):
        new_game.select_piece(pieces[i])
        new_game.place_piece(0, i)

    assert new_game.board.check_victory()

    with pytest.raises(GameEndedError, match="The game is already over."):
        new_game.select_piece(pieces[-1])


def test_get_available_positions_empty(new_game: GameState):
    """A new game should have 16 unique available positions."""
    pos = new_game.board.get_available_positions()
    assert len(pos) == 16
    assert len(pos) == len(set(pos))


def test_get_available_positions_full(game_draw: GameState):
    """A full game should have no available positions."""
    assert len(game_draw.board.get_available_positions()) == 0


def test_get_available_positions_one_move(new_game: GameState):
    """After one placement, 15 available positions should remain."""
    piece = new_game.get_remaining_pieces()[0]
    new_game.select_piece(piece)
    new_game.place_piece(0, 0)
    assert len(new_game.board.get_available_positions()) == 15


def test_get_remaining_pieces_new_game(new_game: GameState):
    """A new game should have 16 unique remaining pieces."""
    pieces = new_game.get_remaining_pieces()
    assert len(pieces) == 16
    assert len(pieces) == len(set(pieces))


def test_get_remaining_pieces_one_selection(new_game: GameState):
    """After one selection, 15 available pieces should remain."""
    piece = new_game.get_remaining_pieces()[0]
    new_game.select_piece(piece)
    assert len(new_game.get_remaining_pieces()) == 15


def test_get_remaining_pieces_full(game_draw: GameState):
    """A full game should have no remaining pieces."""
    assert len(game_draw.get_remaining_pieces()) == 0


def test_new_game_to_str(new_game: GameState):
    """The string representation of a new game should match the expected layout."""
    printed_game = (
        f"Current player: {Player.PLAYER_1}\n"
        f"Phase: {GamePhase.SELECTION}\n"
        ".. | .. | .. | ..\n"
        ".. | .. | .. | ..\n"
        ".. | .. | .. | ..\n"
        ".. | .. | .. | .."
    )
    assert str(new_game) == printed_game


def test_full_board_to_str(game_draw: GameState):
    """The string representation of a full game should match the expected structure."""
    regex = re.compile(r"\d\d \| \d\d \| \d\d \| \d\d")
    lines = str(game_draw).splitlines()
    assert len(lines) >= 6

    printed_player = lines.pop(0)
    assert printed_player.startswith("Current player: ")
    printed_phase = lines.pop(0)
    assert printed_phase.startswith("Phase: ")
    for line in lines:
        assert regex.match(line) is not None


def test_clone_creates_independent_state(new_game: GameState):
    """Cloning a game state should create an independent copy with shared immutable pieces."""
    cloned_game = new_game.clone()

    # Mutable attributes must be new instances
    assert cloned_game is not new_game
    assert cloned_game.board is not new_game.board
    assert cloned_game.remaining_pieces is not new_game.remaining_pieces
    assert cloned_game.board.game_board is not new_game.board.game_board

    # Immutable attributes must be shared
    assert cloned_game.current_player is new_game.current_player
    assert cloned_game.phase is new_game.phase
    assert cloned_game.next_piece is new_game.next_piece
    assert cloned_game.result is new_game.result

    # All Piece objects inside the collections must be identical
    for key, piece in new_game.remaining_pieces.items():
        assert cloned_game.remaining_pieces[key] is piece


def test_clone_mutation_independence(new_game: GameState):
    """Mutating the cloned state should have zero impact on the original state."""
    cloned_game = new_game.clone()

    # Select and place a piece on the clone
    pieces = cloned_game.get_remaining_pieces()
    square = cloned_game.board.get_available_positions()[0]
    cloned_game.select_piece(pieces[0])
    cloned_game.place_piece(*square)
    cloned_game.select_piece(pieces[1])

    # Original phase and next_piece should be untouched
    assert new_game.phase == GamePhase.SELECTION
    assert cloned_game.phase == GamePhase.PLACEMENT
    assert new_game.next_piece is None
    assert cloned_game.next_piece is not None

    # Original remaining_pieces should be untouched
    assert len(new_game.get_remaining_pieces()) == 16
    assert len(cloned_game.get_remaining_pieces()) == 14

    # Original board should be untouched
    assert len(new_game.board.get_available_positions()) == 16
    assert len(cloned_game.board.get_available_positions()) == 15


def test_get_legal_moves_by_phase(new_game: GameState):
    """get_legal_moves returns pieces in SELECTION phase and coordinates in PLACEMENT phase."""
    selection_moves = new_game.get_legal_moves()
    assert len(selection_moves) == 16
    assert all(isinstance(move, Piece) for move in selection_moves)

    first_piece = selection_moves[0]
    assert isinstance(first_piece, Piece)
    new_game.select_piece(first_piece)

    placement_moves = new_game.get_legal_moves()
    assert len(placement_moves) == 16
    assert all(isinstance(move, tuple) for move in placement_moves)


def test_get_legal_moves_empty_after_victory(new_game: GameState):
    """A finished game won early (with remaining pieces) must expose no legal moves."""
    pieces = new_game.get_remaining_pieces()
    for i in range(4):
        new_game.select_piece(pieces[i])
        new_game.place_piece(0, i)

    assert new_game.result is not None
    assert len(new_game.get_remaining_pieces()) == 12
    assert new_game.get_legal_moves() == []


def test_get_legal_moves_empty_after_draw(game_draw: GameState):
    """A drawn game must expose no legal moves."""
    assert game_draw.get_legal_moves() == []


def test_apply_move_valid_transitions(new_game: GameState):
    """apply_move dispatches to select_piece and place_piece according to the active phase."""
    piece = new_game.get_remaining_pieces()[0]
    new_game.apply_move(piece)
    assert new_game.phase == GamePhase.PLACEMENT
    assert new_game.next_piece == piece

    new_game.apply_move((0, 0))
    assert new_game.phase == GamePhase.SELECTION  # type: ignore[comparison-overlap]
    assert new_game.board.game_board[0, 0] == piece


def test_apply_move_wrong_type_raises(new_game: GameState):
    """apply_move raises TypeError when the move type does not match the current phase."""
    with pytest.raises(TypeError, match="Expected Piece for selection"):
        new_game.apply_move((0, 0))

    piece = new_game.get_remaining_pieces()[0]
    new_game.select_piece(piece)
    with pytest.raises(TypeError, match="Expected tuple for placement"):
        new_game.apply_move(piece)


def test_apply_move_game_ended_raises(game_draw: GameState):
    """apply_move raises GameEndedError when called on a finished game."""
    with pytest.raises(GameEndedError, match="The game is already over."):
        game_draw.apply_move((0, 0))
