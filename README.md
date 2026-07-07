# 🧠 Spaced Repetition Engine

A CLI tool for spaced repetition flashcard study powered by the **SM-2 algorithm** (the same scheduling core used by Anki). Create decks, add cards, study with intelligent interval scheduling, and track your retention over time.

## ✨ Features

- **SM-2 scheduling algorithm** — scientifically-backed spaced repetition intervals
- **Deck management** — create, list, and organize study decks
- **Card CRUD** — add, edit, delete flashcards with front/back text
- **Study sessions** — interactive CLI study mode with quality ratings (0–5)
- **Review scheduling** — cards resurface at optimal intervals based on your performance
- **Due-date tracking** — know exactly which cards need review today
- **Statistics** — per-deck and per-card mastery stats (ease factor, interval, reps)
- **JSON persistence** — your decks and progress are saved between sessions
- **Sample decks** — get started instantly with built-in example content

## 📦 Installation

```bash
cd spaced-repetition-engine
pip install -e .
```

## 🚀 Usage

```bash
# See all commands
srs

# Create a deck
srs create-deck --name "Spanish Vocabulary"

# Add cards
srs add-card --deck "Spanish Vocabulary" --front "Hola" --back "Hello"

# List decks
srs decks

# Start studying
srs study --deck "Spanish Vocabulary"

# View statistics
srs stats --deck "Spanish Vocabulary"
```

## 🧪 Tests

```bash
pip install pytest
pytest
```

## 📁 Structure

```
spaced-repetition-engine/
├── spaced_repetition_engine/
│   ├── __init__.py
│   ├── cli.py          # CLI entry point & commands
│   ├── engine.py       # SM-2 algorithm & card management
│   └── storage.py      # JSON persistence
├── tests/
│   └── test_engine.py
├── pyproject.toml
└── README.md
```

## 📐 SM-2 Algorithm

The SuperMemo SM-2 algorithm adjusts each card's:
- **Ease factor** (minimum 1.3) — how easily you recall the card
- **Interval** — days until the card is shown again
- **Repetition count** — consecutive correct recalls

Quality ratings (0–5):
| Rating | Meaning |
|--------|---------|
| 0 | Complete blackout |
| 1 | Incorrect, but felt familiar |
| 2 | Incorrect, but easy to recall after seeing |
| 3 | Correct, but with serious difficulty |
| 4 | Correct, after some hesitation |
| 5 | Perfect recall |

## 📄 License

MIT
