class QuartoError(Exception):
    """Common base class for all Quarto exceptions."""


class GameEndedError(QuartoError):
    """Raised when an action is attempted on a game that is already finished."""


class IllegalMoveError(QuartoError):
    """Base exception for actions that violate the game rules."""


class InvalidPieceError(IllegalMoveError):
    """Raised when attempting to select or play a piece that is no longer available."""


class InvalidSquareError(IllegalMoveError):
    """Raised when attempting to place a piece on an out-of-bounds or already occupied square."""


class InvalidPhaseError(IllegalMoveError):
    """
    Raised when an action does not match the current GamePhase:
        - trying to place a piece during the SELECTION phase.
        - trying to select a piece during the PLACEMENT phase.
    """
