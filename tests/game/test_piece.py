import pytest

from quarto_benchmark.game.piece import Piece, generate_all_pieces


@pytest.mark.parametrize(
    "kwargs",
    [
        {"height": -1, "color": 0, "shape": 0, "fill": 0},
        {"height": 2, "color": 0, "shape": 0, "fill": 0},
        {"height": 0, "color": -1, "shape": 0, "fill": 0},
        {"height": 0, "color": 0, "shape": 3, "fill": 0},
        {"height": 0, "color": 0, "shape": 0, "fill": 42},
        {"height": True, "color": 0, "shape": 0, "fill": 0},
    ],
)
def test_piece_invalid_attribute_raises(kwargs: dict[str, int]):
    """Creating a piece with attributes outside {0, 1} must raise ValueError."""
    with pytest.raises(ValueError, match="must be 0 or 1"):
        Piece(**kwargs)


def test_piece_to_bits_zeros():
    """A piece with all attributes set to 0 must map to 0."""
    piece = Piece(0, 0, 0, 0)
    assert piece.to_bits() == 0


def test_piece_to_bits_ones():
    """A piece with all attributes set to 1 must map to 15."""
    piece = Piece(1, 1, 1, 1)
    assert piece.to_bits() == 15


def test_piece_to_str_zeros():
    """A piece with all attributes set to 0 must print as 00."""
    piece = Piece(0, 0, 0, 0)
    assert str(piece) == "00"


def test_piece_to_str_ones():
    """A piece with all attributes set to 1 must print as 15."""
    piece = Piece(1, 1, 1, 1)
    assert str(piece) == "15"


def test_generate_all_pieces():
    """generate_all_pieces should create 16 pieces object."""
    pieces = generate_all_pieces()
    assert len(pieces) == 16
    assert all(isinstance(p, Piece) for p in pieces)


def test_generate_all_pieces_unique_bits():
    """Generated pieces should cover only unique piece values."""
    pieces = generate_all_pieces()
    pieces_bits = [p.to_bits() for p in pieces]
    assert len(pieces_bits) == len(set(pieces_bits))


def test_generate_all_pieces_every_combinations():
    """Generated pieces should cover all values between 0 to 15."""
    pieces = generate_all_pieces()
    pieces_bits = [p.to_bits() for p in pieces]
    pieces_bits.sort()
    assert pieces_bits == list(range(16))
