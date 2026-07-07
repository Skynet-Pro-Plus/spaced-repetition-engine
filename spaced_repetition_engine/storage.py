"""JSON-backed storage for the spaced repetition engine.

Decks and cards are persisted as JSON.  Each deck file contains a list of
card dictionaries with their SM-2 scheduling metadata.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List

DEFAULT_DATA_DIR = Path.home() / ".spaced_repetition"
DECK_INDEX_FILE = "decks.json"


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def load_deck_index(data_dir: str | Path | None = None) -> Dict[str, str]:
    """Return {deck_name: filename} mapping."""
    directory = Path(data_dir) if data_dir else DEFAULT_DATA_DIR
    filepath = directory / DECK_INDEX_FILE
    if not filepath.exists():
        return {}
    try:
        with open(filepath, "r", encoding="utf-8") as fh:
            data = json.load(fh)
            return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, OSError):
        return {}


def save_deck_index(index: Dict[str, str], data_dir: str | Path | None = None) -> None:
    directory = Path(data_dir) if data_dir else DEFAULT_DATA_DIR
    _ensure_dir(directory)
    filepath = directory / DECK_INDEX_FILE
    with open(filepath, "w", encoding="utf-8") as fh:
        json.dump(index, fh, indent=2)


def load_deck(deck_name: str, data_dir: str | Path | None = None) -> List[Dict[str, Any]]:
    """Load cards from a deck file."""
    directory = Path(data_dir) if data_dir else DEFAULT_DATA_DIR
    index = load_deck_index(data_dir)
    filename = index.get(deck_name, f"{deck_name.replace(' ', '_').lower()}.json")
    filepath = directory / filename
    if not filepath.exists():
        return []
    try:
        with open(filepath, "r", encoding="utf-8") as fh:
            data = json.load(fh)
            return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def save_deck(deck_name: str, cards: List[Dict[str, Any]], data_dir: str | Path | None = None) -> None:
    """Persist cards for a deck."""
    directory = Path(data_dir) if data_dir else DEFAULT_DATA_DIR
    _ensure_dir(directory)
    index = load_deck_index(data_dir)
    filename = index.get(deck_name, f"{deck_name.replace(' ', '_').lower()}.json")
    filepath = directory / filename
    with open(filepath, "w", encoding="utf-8") as fh:
        json.dump(cards, fh, indent=2, default=str)
    # Update index
    if deck_name not in index:
        index[deck_name] = filename
        save_deck_index(index, data_dir)


def clear_all(data_dir: str | Path | None = None) -> None:
    """Remove all deck files (used in tests)."""
    directory = Path(data_dir) if data_dir else DEFAULT_DATA_DIR
    index = load_deck_index(data_dir)
    for deck_name, filename in index.items():
        filepath = directory / filename
        if filepath.exists():
            os.remove(filepath)
    idx_file = directory / DECK_INDEX_FILE
    if idx_file.exists():
        os.remove(idx_file)
