"""Tests for the Spaced Repetition Engine."""

import os
import sys
from datetime import datetime, timedelta, timezone

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from spaced_repetition_engine.engine import (
    sm2,
    make_card,
    review_card,
    is_due,
    SRSEngine,
)
from spaced_repetition_engine import cli


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def engine(tmp_path):
    return SRSEngine(data_dir=str(tmp_path))


# ---------------------------------------------------------------------------
# SM-2 Algorithm tests
# ---------------------------------------------------------------------------
def test_sm2_perfect_recall_first():
    """First perfect recall: reps=1, interval=1."""
    reps, ease, interval = sm2(quality=5, repetitions=0, ease_factor=2.5, interval=0)
    assert reps == 1
    assert interval == 1
    assert ease >= 2.5  # ease should increase or stay for quality=5


def test_sm2_second_recall():
    """Second correct recall: interval=6."""
    reps, ease, interval = sm2(quality=4, repetitions=1, ease_factor=2.5, interval=1)
    assert reps == 2
    assert interval == 6


def test_sm2_third_recall_uses_ease():
    """Third+ recall: interval = round(prev_interval * ease)."""
    reps, ease, interval = sm2(quality=5, repetitions=2, ease_factor=2.5, interval=6)
    assert reps == 3
    expected = round(6 * 2.6)  # ease increases with quality=5
    assert interval == expected


def test_sm2_fail_resets():
    """Quality < 3 resets repetitions to 0."""
    reps, ease, interval = sm2(quality=2, repetitions=5, ease_factor=2.8, interval=30)
    assert reps == 0
    assert interval == 1


def test_sm2_ease_min():
    """Ease factor should never go below 1.3."""
    reps, ease, interval = sm2(quality=0, repetitions=3, ease_factor=1.4, interval=10)
    assert ease >= 1.3


def test_sm2_invalid_quality():
    with pytest.raises(ValueError):
        sm2(quality=6, repetitions=0, ease_factor=2.5, interval=0)
    with pytest.raises(ValueError):
        sm2(quality=-1, repetitions=0, ease_factor=2.5, interval=0)


# ---------------------------------------------------------------------------
# Card tests
# ---------------------------------------------------------------------------
def test_make_card_defaults():
    card = make_card("Question?", "Answer!")
    assert card["front"] == "Question?"
    assert card["back"] == "Answer!"
    assert card["repetitions"] == 0
    assert card["ease_factor"] == 2.5
    assert card["interval"] == 0
    assert "id" in card
    assert "due" in card


def test_review_card_good_quality():
    card = make_card("Q", "A")
    updated = review_card(card, quality=5)
    assert updated["repetitions"] == 1
    assert updated["interval"] == 1
    assert updated["last_reviewed"] is not None


def test_review_card_bad_quality():
    card = make_card("Q", "A")
    card["repetitions"] = 3
    card["interval"] = 15
    updated = review_card(card, quality=1)
    assert updated["repetitions"] == 0
    assert updated["interval"] == 1


def test_is_due_new_card():
    """New cards should be due immediately."""
    card = make_card("Q", "A")
    assert is_due(card) is True


def test_is_due_future():
    """Card with future due date should not be due."""
    card = make_card("Q", "A")
    future = (datetime.now(timezone.utc) + timedelta(days=5)).isoformat()
    card["due"] = future
    assert is_due(card) is False


def test_is_due_past():
    card = make_card("Q", "A")
    past = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    card["due"] = past
    assert is_due(card) is True


# ---------------------------------------------------------------------------
# Engine / Deck tests
# ---------------------------------------------------------------------------
def test_welcome_message_prints(capsys):
    """CLI prints welcome banner with no command."""
    result = cli.main([])
    captured = capsys.readouterr()
    assert result == 0
    assert "Spaced Repetition Engine" in captured.out


def test_create_deck(engine):
    assert engine.create_deck("Spanish") is True
    assert engine.create_deck("Spanish") is False  # duplicate


def test_add_card(engine):
    engine.create_deck("Test")
    card = engine.add_card("Test", "Front", "Back")
    assert card is not None
    assert card["front"] == "Front"
    assert len(engine.get_deck("Test")) == 1


def test_add_card_nonexistent_deck(engine):
    card = engine.add_card("Nope", "F", "B")
    assert card is None


def test_remove_card(engine):
    engine.create_deck("Test")
    card = engine.add_card("Test", "F", "B")
    assert engine.remove_card("Test", card["id"]) is True
    assert len(engine.get_deck("Test")) == 0


def test_remove_card_nonexistent(engine):
    engine.create_deck("Test")
    assert engine.remove_card("Test", 999) is False


def test_get_due_cards(engine):
    engine.create_deck("Test")
    engine.add_card("Test", "Q1", "A1")
    engine.add_card("Test", "Q2", "A2")
    due = engine.get_due_cards("Test")
    assert len(due) == 2  # new cards are due immediately


def test_review_updates_card(engine):
    engine.create_deck("Test")
    card = engine.add_card("Test", "Q", "A")
    updated = engine.review("Test", card["id"], quality=5)
    assert updated is not None
    assert updated["repetitions"] == 1


def test_review_nonexistent_card(engine):
    engine.create_deck("Test")
    result = engine.review("Test", 999, quality=5)
    assert result is None


def test_get_stats_empty(engine):
    engine.create_deck("Empty")
    stats = engine.get_stats("Empty")
    assert stats["total_cards"] == 0
    assert stats["due_cards"] == 0


def test_get_stats_with_cards(engine):
    engine.create_deck("Test")
    engine.add_card("Test", "Q1", "A1")
    engine.add_card("Test", "Q2", "A2")
    stats = engine.get_stats("Test")
    assert stats["total_cards"] == 2
    assert stats["due_cards"] == 2
    assert stats["mastered_cards"] == 0


def test_persistence(tmp_path):
    """Decks and cards persist across engine instances."""
    e1 = SRSEngine(data_dir=str(tmp_path))
    e1.create_deck("Persist")
    e1.add_card("Persist", "Q", "A")
    e2 = SRSEngine(data_dir=str(tmp_path))
    assert "Persist" in [d["name"] for d in e2.list_decks()]
    assert len(e2.get_deck("Persist")) == 1


def test_sample_deck(engine):
    name = engine.load_sample_deck()
    assert name == "Python Basics"
    cards = engine.get_deck(name)
    assert len(cards) >= 5


def test_list_decks(engine):
    engine.create_deck("A")
    engine.create_deck("B")
    decks = engine.list_decks()
    names = [d["name"] for d in decks]
    assert "A" in names
    assert "B" in names


def test_delete_deck(engine):
    engine.create_deck("ToDelete")
    assert engine.delete_deck("ToDelete") is True
    assert engine.delete_deck("ToDelete") is False
