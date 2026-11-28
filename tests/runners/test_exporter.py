import logging
from pathlib import Path

import pytest

from quarto_benchmark.players.ai.random_ai import RandomAI
from quarto_benchmark.runners.exporter import ConsoleExporter, MarkdownExporter
from quarto_benchmark.runners.tournament_runner import (
    ChampionshipResult,
    LeaderboardEntry,
    MatchupResult,
)


@pytest.fixture
def sample_matchup() -> MatchupResult:
    """Sample 1v1 matchup result."""
    return {
        "player_a_name": "AI-A",
        "player_b_name": "AI-B",
        "games_per_side": 5,
        "total_games": 10,
        "a_wins": 6,
        "b_wins": 3,
        "draws": 1,
        "starter_wins": 5,
        "follower_wins": 4,
    }


@pytest.fixture
def sample_championship(sample_matchup: MatchupResult) -> ChampionshipResult:
    """Sample championship result with fractional Elo scores to check rounding."""
    leaderboard: list[LeaderboardEntry] = [
        {
            "player": RandomAI("AI-A"),
            "wins": 6,
            "draws": 1,
            "losses": 3,
            "total_games": 10,
            "elo": 1549.6,
        },
        {
            "player": RandomAI("AI-B"),
            "wins": 3,
            "draws": 1,
            "losses": 6,
            "total_games": 10,
            "elo": 1450.4,
        },
    ]
    return {"leaderboard": leaderboard, "matchups": [sample_matchup]}


def test_console_print_matchup_report(
    sample_matchup: MatchupResult, caplog: pytest.LogCaptureFixture
) -> None:
    """ConsoleExporter should log matchup stats with Player 1 / Player 2 labels."""
    with caplog.at_level(logging.INFO, logger="quarto_benchmark.exporter"):
        ConsoleExporter.print_matchup_report(sample_matchup)

    assert "MATCHUP REPORT: AI-A vs AI-B" in caplog.text
    assert "AI-A Wins: 6 (60.0%)" in caplog.text
    assert "AI-B Wins: 3 (30.0%)" in caplog.text
    assert "Player 1 (Starter) Wins:  5 (50.0%)" in caplog.text
    assert "Player 2 (Follower) Wins: 4 (40.0%)" in caplog.text


def test_console_print_championship_report(
    sample_championship: ChampionshipResult, caplog: pytest.LogCaptureFixture
) -> None:
    """ConsoleExporter should log the leaderboard with rounded Elo values."""
    with caplog.at_level(logging.INFO, logger="quarto_benchmark.exporter"):
        ConsoleExporter.print_championship_report(sample_championship["leaderboard"])

    assert "CHAMPIONSHIP LEADERBOARD" in caplog.text
    assert "AI-A" in caplog.text
    assert "1550" in caplog.text
    assert "1450" in caplog.text


def test_markdown_generate_report(sample_championship: ChampionshipResult, tmp_path: Path) -> None:
    """MarkdownExporter should create the report file with all benchmark sections."""
    report_path = tmp_path / "reports" / "results.md"
    methodology = "- **Games per side**: 5"

    MarkdownExporter.generate_report(sample_championship, report_path, methodology=methodology)

    assert report_path.exists()
    content = report_path.read_text(encoding="utf-8")
    assert "# Quarto AI Benchmark Results" in content
    assert "## Methodology" in content
    assert "- **Games per side**: 5" in content
    assert "| 1 | **AI-A** | 1550 (+50) | 6 (60.0%) | 1 (10.0%) | 3 (30.0%) |" in content
    assert "| 2 | **AI-B** | 1450 (-50) | 3 (30.0%) | 1 (10.0%) | 6 (60.0%) |" in content
    assert "## Head-to-Head Win Rate Matrix" in content
    assert "| AI-A vs AI-B | 10 | 6 (60.0%) | 3 (30.0%) | 1 (10.0%) |" in content
    assert "## Starting-Player Bias Analysis" in content
    assert "| Player 1 (Starter) | 5 | 50.0% |" in content


def test_markdown_generate_report_zero_games(tmp_path: Path) -> None:
    """MarkdownExporter should handle zero-game matchups without dividing by zero."""
    empty_matchup: MatchupResult = {
        "player_a_name": "AI-A",
        "player_b_name": "AI-B",
        "games_per_side": 0,
        "total_games": 0,
        "a_wins": 0,
        "b_wins": 0,
        "draws": 0,
        "starter_wins": 0,
        "follower_wins": 0,
    }
    results: ChampionshipResult = {
        "leaderboard": [
            {
                "player": RandomAI("AI-A"),
                "wins": 0,
                "draws": 0,
                "losses": 0,
                "total_games": 0,
                "elo": 1500.0,
            }
        ],
        "matchups": [empty_matchup],
    }
    report_path = tmp_path / "empty.md"

    MarkdownExporter.generate_report(results, report_path)

    content = report_path.read_text(encoding="utf-8")
    assert "1500 (=)" in content
    assert "N/A" in content
    assert "## Starting-Player Bias Analysis" not in content
