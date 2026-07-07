"""Core SM-2 spaced repetition algorithm and deck/card management.

This module implements the SuperMemo SM-2 algorithm for scheduling flashcard
reviews.  It is framework-free and fully unit-testable.
"""

from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from . import storage


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _utc_now_iso() -> str:
    return _utc_now().isoformat()


# ---------------------------------------------------------------------------
# SM-2 Algorithm
# ---------------------------------------------------------------------------
def sm2(
    quality: int,
    repetitions: int,
    ease_factor: float,
    interval: int,
) -> Tuple[int, float, int]:
    """Core SM-2 algorithm.

    Parameters
    ----------
    quality : int
        Quality of the response (0–5).
    repetitions : int
        Number of consecutive correct repetitions.
    ease_factor : float
        Current ease factor (≥ 1.3).
    interval : int
        Current interval in days.

    Returns
    -------
    tuple (new_repetitions, new_ease_factor, new_interval)
    """
    if quality < 0 or quality > 5:
        raise ValueError("Quality must be an integer from 0 to 5.")

    # If quality < 3, reset repetitions
    if quality < 3:
        new_repetitions = 0
        new_interval = 1
    else:
        new_repetitions = repetitions + 1
        if new_repetitions == 1:
            new_interval = 1
        elif new_repetitions == 2:
            new_interval = 6
        else:
            new_interval = round(interval * ease_factor)

    # Update ease factor
    new_ease = ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    if new_ease < 1.3:
        new_ease = 1.3

    return new_repetitions, round(new_ease, 3), new_interval


# ---------------------------------------------------------------------------
# Card helpers
# ---------------------------------------------------------------------------
def make_card(front: str, back: str, tags: Optional[List[str]] = None) -> Dict[str, Any]:
    """Create a new card dict with SM-2 defaults."""
    return {
        "id": abs(hash(front + back + _utc_now_iso())) % (10**10),
        "front": front,
        "back": back,
        "tags": tags or [],
        "repetitions": 0,
        "ease_factor": 2.5,
        "interval": 0,
        "due": _utc_now_iso(),  # due immediately
        "created": _utc_now_iso(),
        "last_reviewed": None,
    }


def review_card(card: Dict[str, Any], quality: int) -> Dict[str, Any]:
    """Apply SM-2 to a card and update its scheduling fields."""
    reps, ease, interval = sm2(
        quality=quality,
        repetitions=card.get("repetitions", 0),
        ease_factor=card.get("ease_factor", 2.5),
        interval=card.get("interval", 0),
    )
    card["repetitions"] = reps
    card["ease_factor"] = ease
    card["interval"] = interval
    now = _utc_now()
    due = now + timedelta(days=interval)
    card["due"] = due.isoformat()
    card["last_reviewed"] = now.isoformat()
    return card


def is_due(card: Dict[str, Any], now: Optional[datetime] = None) -> bool:
    """Check whether a card is due for review."""
    if now is None:
        now = _utc_now()
    try:
        due_date = datetime.fromisoformat(card["due"])
        if due_date.tzinfo is None:
            due_date = due_date.replace(tzinfo=timezone.utc)
        return now >= due_date
    except (KeyError, ValueError, TypeError):
        return True  # If we can't parse, treat as due


# ---------------------------------------------------------------------------
# Deck class
# ---------------------------------------------------------------------------
class SRSEngine:
    """High-level interface for managing decks and study sessions."""

    def __init__(self, data_dir: Optional[str] = None) -> None:
        self.data_dir = data_dir
        self._decks: Dict[str, List[Dict[str, Any]]] = {}
        self._load_all()

    def _load_all(self) -> None:
        index = storage.load_deck_index(data_dir=self.data_dir)
        for deck_name in index:
            self._decks[deck_name] = storage.load_deck(deck_name, data_dir=self.data_dir)

    # -- Deck operations --
    def create_deck(self, name: str) -> bool:
        """Create a new deck.  Returns False if it already exists."""
        if name in self._decks:
            return False
        self._decks[name] = []
        self._save_deck(name)
        return True

    def list_decks(self) -> List[Dict[str, Any]]:
        """Return a summary list of all decks."""
        result = []
        for name, cards in self._decks.items():
            due_count = sum(1 for c in cards if is_due(c))
            result.append({
                "name": name,
                "total_cards": len(cards),
                "due_cards": due_count,
            })
        return result

    def get_deck(self, name: str) -> List[Dict[str, Any]]:
        """Return cards for a deck (or empty list if not found)."""
        return self._decks.get(name, [])

    def delete_deck(self, name: str) -> bool:
        """Delete a deck.  Returns True if it existed."""
        if name not in self._decks:
            return False
        del self._decks[name]
        # Remove from storage
        index = storage.load_deck_index(data_dir=self.data_dir)
        filename = index.pop(name, None)
        if filename:
            storage.save_deck_index(index, data_dir=self.data_dir)
            directory = storage.DEFAULT_DATA_DIR if not self.data_dir else __import__("pathlib").Path(self.data_dir)
            filepath = directory / filename
            if filepath.exists():
                filepath.unlink()
        return True

    # -- Card operations --
    def add_card(
        self,
        deck_name: str,
        front: str,
        back: str,
        tags: Optional[List[str]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Add a card to a deck.  Returns the card or None if deck doesn't exist."""
        if deck_name not in self._decks:
            return None
        card = make_card(front, back, tags)
        self._decks[deck_name].append(card)
        self._save_deck(deck_name)
        return card

    def remove_card(self, deck_name: str, card_id: int) -> bool:
        """Remove a card by ID.  Returns True if found and removed."""
        if deck_name not in self._decks:
            return False
        before = len(self._decks[deck_name])
        self._decks[deck_name] = [c for c in self._decks[deck_name] if c["id"] != card_id]
        if len(self._decks[deck_name]) < before:
            self._save_deck(deck_name)
            return True
        return False

    def get_due_cards(self, deck_name: str) -> List[Dict[str, Any]]:
        """Return all due cards for a deck."""
        if deck_name not in self._decks:
            return []
        return [c for c in self._decks[deck_name] if is_due(c)]

    def review(self, deck_name: str, card_id: int, quality: int) -> Optional[Dict[str, Any]]:
        """Review a card with a quality rating (0–5). Returns updated card or None."""
        if deck_name not in self._decks:
            return None
        for card in self._decks[deck_name]:
            if card["id"] == card_id:
                review_card(card, quality)
                self._save_deck(deck_name)
                return card
        return None

    def get_stats(self, deck_name: str) -> Dict[str, Any]:
        """Return aggregate statistics for a deck."""
        cards = self._decks.get(deck_name, [])
        if not cards:
            return {
                "deck": deck_name,
                "total_cards": 0,
                "due_cards": 0,
                "mastered_cards": 0,
                "avg_ease": 0.0,
                "avg_interval": 0.0,
            }

        due = sum(1 for c in cards if is_due(c))
        mastered = sum(1 for c in cards if c.get("repetitions", 0) >= 3)
        avg_ease = sum(c.get("ease_factor", 2.5) for c in cards) / len(cards)
        avg_interval = sum(c.get("interval", 0) for c in cards) / len(cards)

        return {
            "deck": deck_name,
            "total_cards": len(cards),
            "due_cards": due,
            "mastered_cards": mastered,
            "avg_ease": round(avg_ease, 2),
            "avg_interval": round(avg_interval, 1),
        }

    # -- Internal --
    def _save_deck(self, name: str) -> None:
        storage.save_deck(name, self._decks[name], data_dir=self.data_dir)

    # -- Sample data --
    def load_sample_deck(self) -> str:
        """Create a sample 'Python Basics' deck for first-time users."""
        deck_name = "Python Basics"
        if deck_name not in self._decks:
            self.create_deck(deck_name)
        if not self._decks[deck_name]:
            samples = [
                ("What is a list comprehension?", "A concise way to create lists: [x*2 for x in range(10)]"),
                ("What does len() do?", "Returns the number of items in an object (list, string, dict, etc.)"),
                ("What is a dictionary?", "An unordered collection of key-value pairs, defined with {}"),
                ("What does the 'self' parameter do?", "Refers to the current instance of a class in methods."),
                ("What is PEP 8?", "Python's official style guide for writing readable code."),
                ("What is a lambda function?", "A small anonymous function: lambda x: x + 1"),
                ("What does pip do?", "Python's package installer — used to install libraries from PyPI."),
                ("What is __init__.py?", "A file that marks a directory as a Python package."),
            ]
            for front, back in samples:
                self.add_card(deck_name, front, back)
        return deck_name
