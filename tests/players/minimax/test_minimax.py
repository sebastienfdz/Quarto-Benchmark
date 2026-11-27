import pytest

from quarto_benchmark.game.state import GameState
from quarto_benchmark.game.types import GameResult, Player
from quarto_benchmark.players.ai.minimax.evaluator import WIN_SCORE, SimpleEvaluator
from quarto_benchmark.players.ai.minimax.minimax import Minimax


# Fixture GameState
@pytest.fixture
def new_game() -> GameState:
    """Create a new game of Quarto (Phase = SELECTION)"""
    game = GameState()
    return game


@pytest.fixture
def winning_game() -> GameState:
    """
    Create a new game of Quarto with a winning move (Phase = SELECTION).
    Adding the piece (0, 0, 0, 0) in the square (0, 0) is winning.
    """
    game = GameState()
    pieces = game.get_remaining_pieces()

    for x in range(1, 4):
        game.select_piece(pieces[x])
        game.place_piece(x, 0)

    assert game.result is None
    return game


@pytest.fixture
def mid_game() -> GameState:
    """Create a new game of Quarto in the middle of the game (Phase = PLACEMENT)."""
    game = GameState()
    pieces = game.get_remaining_pieces()
    moves = [
        (pieces[0], (0, 0)),
        (pieces[1], (1, 1)),
        (pieces[2], (2, 2)),
    ]

    for piece, (x, y) in moves:
        game.select_piece(piece)
        game.place_piece(x, y)

    assert game.result is None
    return game


# Fixture Minimax
@pytest.fixture(params=[False, True], ids=["Naive", "AlphaBeta"])
def minimax_player(request) -> Minimax:
    """A Minimax player parameterized to test both Naive and Alpha-Beta modes."""
    evaluator = SimpleEvaluator()
    return Minimax(evaluator=evaluator, depth=2, use_alpha_beta=request.param)


def test_choose_piece_valid(new_game: GameState, minimax_player: Minimax):
    """The AI should select a valid available piece from the pool."""
    piece = minimax_player.choose_piece(new_game)
    assert piece in new_game.get_remaining_pieces()


def test_choose_piece_not_winning(winning_game: GameState, minimax_player: Minimax):
    """
    In a situation where the opponent could win, the AI
    must not choose the piece that completes the Quarto.
    """
    loosing_piece = winning_game.get_remaining_pieces()[0]
    chosen_piece = minimax_player.choose_piece(winning_game)
    assert chosen_piece != loosing_piece


def test_choose_position_valid(new_game: GameState, minimax_player: Minimax):
    """The AI should select an valid empty square on the board."""
    piece = new_game.get_remaining_pieces()[0]
    new_game.select_piece(piece)

    x, y = minimax_player.choose_position(new_game, piece)
    assert (x, y) in new_game.board.get_available_positions()


def test_choose_position_winning(winning_game: GameState, minimax_player: Minimax):
    """The AI must select the winning square when handed a winning piece."""
    winning_piece = winning_game.get_remaining_pieces()[0]
    winning_game.select_piece(winning_piece)

    x, y = minimax_player.choose_position(winning_game, winning_piece)
    assert (x, y) == (0, 0)


@pytest.mark.parametrize("depth", [2, 4])
def test_alpha_beta_pruning_reduces_evaluations(
    winning_game: GameState, monkeypatch: pytest.MonkeyPatch, depth: int
):
    """Verify that Alpha-Beta pruning evaluates strictly fewer nodes than Naive Minimax."""
    # Mock evaluator to count node evaluations
    evaluator = SimpleEvaluator()
    original_evaluate = evaluator.evaluate
    eval_count = 0

    def mock_count_evaluate(state: GameState) -> float:
        nonlocal eval_count
        eval_count += 1
        return original_evaluate(state)

    monkeypatch.setattr(evaluator, "evaluate", mock_count_evaluate)

    # Test with naive minimax
    naive_minimax = Minimax(evaluator=evaluator, depth=depth, use_alpha_beta=False)
    naive_minimax.choose_piece(winning_game.clone())
    naive_count = eval_count

    eval_count = 0

    # Test with minimax with alpha-beta pruning
    ab_minimax = Minimax(evaluator=evaluator, depth=depth, use_alpha_beta=True)
    ab_minimax.choose_piece(winning_game.clone())
    ab_count = eval_count

    assert ab_count < naive_count, (
        f"Alpha-Beta ({ab_count}) should evaluate fewer nodes than Naive ({naive_count})."
    )


@pytest.mark.parametrize("invalid_depth", [0, -1])
def test_minimax_invalid_depth_raises(invalid_depth: int):
    """Initializing Minimax with depth < 1 must raise ValueError."""
    with pytest.raises(ValueError, match="Search depth must be at least 1"):
        Minimax(evaluator=SimpleEvaluator(), depth=invalid_depth)


def test_alpha_beta_matches_naive_move(mid_game: GameState):
    """Alpha-Beta pruning must return the exact same move as Naive Minimax."""
    evaluator = SimpleEvaluator()
    naive = Minimax(evaluator=evaluator, depth=3, use_alpha_beta=False)
    ab = Minimax(evaluator=evaluator, depth=3, use_alpha_beta=True)

    assert ab.choose_piece(mid_game.clone()) == naive.choose_piece(mid_game.clone())


def test_depth_weighted_terminal_scores():
    """Faster wins score higher than slower wins, and slower losses higher than fast losses."""
    minimax = Minimax(evaluator=SimpleEvaluator(), depth=4)
    win_p1 = GameState()
    win_p1.result = GameResult.PLAYER_1

    assert minimax._evaluate_for_maximizer(win_p1, Player.PLAYER_1, depth=3) == WIN_SCORE + 3
    assert minimax._evaluate_for_maximizer(win_p1, Player.PLAYER_1, depth=1) == WIN_SCORE + 1
    assert minimax._evaluate_for_maximizer(win_p1, Player.PLAYER_2, depth=3) == -(WIN_SCORE + 3)
    assert minimax._evaluate_for_maximizer(win_p1, Player.PLAYER_2, depth=1) == -(WIN_SCORE + 1)


def test_minimax_no_legal_moves_raises(new_game: GameState):
    """Searching from a finished game with no legal moves must raise ValueError."""
    new_game.result = GameResult.DRAW
    minimax = Minimax(evaluator=SimpleEvaluator(), depth=1)
    with pytest.raises(ValueError, match="No legal moves available"):
        minimax.choose_piece(new_game)
