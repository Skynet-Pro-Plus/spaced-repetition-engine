# Spaced Repetition Engine

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](#license)
[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![Status: Beta](https://img.shields.io/badge/Status-Beta-yellow.svg)](#status)
[![Algorithm: SM-2](https://img.shields.io/badge/Algorithm-SM--2-purple.svg)](#sm-2-algorithm)

> A CLI flashcard study tool powered by the SM-2 spaced repetition algorithm — the same scheduling core used by Anki. Create decks, add cards, study with intelligent interval scheduling, and track retention over time.

---

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Quick Start](#quick-start)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [SM-2 Algorithm](#sm-2-algorithm)
- [Tech Stack](#tech-stack)
- [Testing](#testing)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

Spaced Repetition Engine is a command-line flashcard application that implements the SuperMemo SM-2 algorithm for optimal review scheduling. Study sessions present cards at scientifically-determined intervals, adjusting ease factors and repetition counts based on your recall quality. All data is stored locally as JSON.

## Key Features

- **SM-2 scheduling algorithm** — scientifically-backed spaced repetition intervals
- **Deck management** — create, list, and organize study decks
- **Card CRUD** — add, edit, and delete flashcards with front/back text
- **Interactive study sessions** — CLI study mode with quality ratings (0–5)
- **Review scheduling** — cards resurface at optimal intervals based on performance
- **Due-date tracking** — know exactly which cards need review today
- **Statistics** — per-deck and per-card mastery stats (ease factor, interval, reps)
- **JSON persistence** — decks and progress saved between sessions
- **Sample decks** — get started instantly with built-in example content

## Quick Start

### Prerequisites

- Python 3.8 or higher

### Installation

```bash
git clone https://github.com/Skynet-Pro-Plus/spaced-repetition-engine.git
cd spaced-repetition-engine
pip install -e .
```

## Usage

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

## Project Structure

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

## SM-2 Algorithm

The SuperMemo SM-2 algorithm adjusts each card's:

- **Ease factor** (minimum 1.3) — how easily you recall the card
- **Interval** — days until the card is shown again
- **Repetition count** — consecutive correct recalls

### Quality Ratings

| Rating | Meaning |
|--------|---------|
| 0 | Complete blackout |
| 1 | Incorrect, but felt familiar |
| 2 | Incorrect, but easy to recall after seeing |
| 3 | Correct, but with serious difficulty |
| 4 | Correct, after some hesitation |
| 5 | Perfect recall |

## Tech Stack

- **Language:** Python 3.8+
- **CLI Framework:** argparse
- **Algorithm:** SuperMemo SM-2
- **Storage:** JSON (local file)
- **Testing:** pytest

## Testing

```bash
pip install pytest
pytest
```

## Contributing

1. Fork the repository.
2. Create a feature branch (`git checkout -b feature/your-feature`).
3. Commit your changes (`git commit -m 'Add your feature'`).
4. Push to the branch (`git push origin feature/your-feature`).
5. Open a Pull Request.

## License

This project is licensed under the MIT License.
