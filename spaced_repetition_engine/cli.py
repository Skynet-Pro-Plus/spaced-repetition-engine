"""Command-line interface for Spaced Repetition Engine."""

from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from .engine import SRSEngine

WELCOME = r"""
  ╔══════════════════════════════════════════════╗
  ║  🧠  Spaced Repetition Engine  v1.0.0       ║
  ║      Study smarter with SM-2 scheduling       ║
  ╚══════════════════════════════════════════════╝
"""


def cmd_create_deck(args: argparse.Namespace, engine: SRSEngine) -> int:
    if engine.create_deck(args.name):
        print(f"  ✅ Created deck: {args.name}")
        return 0
    print(f"  ⚠️  Deck '{args.name}' already exists.")
    return 1


def cmd_decks(args: argparse.Namespace, engine: SRSEngine) -> int:
    decks = engine.list_decks()
    if not decks:
        print("  No decks found. Create one with 'srs create-deck --name <deck>'")
        return 0
    print(f"\n  {'Deck':<30s}  {'Cards':>6s}  {'Due':>6s}")
    print("  " + "-" * 50)
    for d in decks:
        print(f"  {d['name']:<30s}  {d['total_cards']:>6d}  {d['due_cards']:>6d}")
    print()
    return 0


def cmd_add_card(args: argparse.Namespace, engine: SRSEngine) -> int:
    tags = [t.strip() for t in args.tags.split(",")] if args.tags else []
    card = engine.add_card(args.deck, args.front, args.back, tags=tags or None)
    if card:
        print(f"  ✅ Added card to '{args.deck}': {args.front[:40]}")
        return 0
    print(f"  ❌ Deck '{args.deck}' not found.")
    return 1


def cmd_list_cards(args: argparse.Namespace, engine: SRSEngine) -> int:
    cards = engine.get_deck(args.deck)
    if not cards:
        print(f"  No cards in '{args.deck}'.")
        return 0
    print(f"\n  Cards in '{args.deck}':\n")
    for c in cards:
        from .engine import is_due
        due_marker = "📌" if is_due(c) else "  "
        print(f"  {due_marker} [{c['id']}]  {c['front'][:50]}")
        print(f"       → {c['back'][:50]}")
        print(f"       reps={c['repetitions']}  ease={c['ease_factor']}  interval={c['interval']}d")
        print()
    return 0


def cmd_study(args: argparse.Namespace, engine: SRSEngine) -> int:
    due = engine.get_due_cards(args.deck)
    if not due:
        print(f"  🎉 No cards due in '{args.deck}'. Come back later!")
        return 0

    print(f"\n  📖 Studying '{args.deck}' — {len(due)} card(s) due\n")

    QUALITY_LABELS = {
        0: "Again (complete blackout)",
        1: "Again (incorrect)",
        2: "Hard (barely correct)",
        3: "Hard (correct, difficult)",
        4: "Good (correct, some hesitation)",
        5: "Easy (perfect recall)",
    }

    reviewed = 0
    for i, card in enumerate(due, 1):
        print(f"  ────────────────────────────────────────────────")
        print(f"  Card {i}/{len(due)}")
        print(f"  ┌─────────────────────────────────────────────┐")
        print(f"  │  {card['front']}")
        print(f"  └─────────────────────────────────────────────┘")
        input("  Press Enter to reveal answer...")
        print(f"\n  ➜  {card['back']}\n")

        print("  How well did you recall it?")
        for q, label in QUALITY_LABELS.items():
            print(f"    {q} — {label}")
        try:
            quality = int(input("\n  Rating (0-5): "))
            if quality < 0 or quality > 5:
                print("  ⚠️  Invalid rating. Defaulting to 3.")
                quality = 3
        except (ValueError, EOFError):
            quality = 3

        engine.review(args.deck, card["id"], quality)
        reviewed += 1
        print(f"  → Next review in {card['interval']} day(s)\n")

    print(f"  ✅ Session complete! Reviewed {reviewed} card(s).")
    return 0


def cmd_stats(args: argparse.Namespace, engine: SRSEngine) -> int:
    stats = engine.get_stats(args.deck)
    print(f"\n  📊 Stats for '{args.deck}'")
    print(f"  " + "=" * 40)
    print(f"  Total cards:    {stats['total_cards']}")
    print(f"  Due now:        {stats['due_cards']}")
    print(f"  Mastered (≥3):  {stats['mastered_cards']}")
    print(f"  Avg ease:       {stats['avg_ease']}")
    print(f"  Avg interval:   {stats['avg_interval']} days")
    return 0


def cmd_sample(args: argparse.Namespace, engine: SRSEngine) -> int:
    name = engine.load_sample_deck()
    print(f"  ✅ Loaded sample deck: {name}")
    return 0


def cmd_delete_card(args: argparse.Namespace, engine: SRSEngine) -> int:
    if engine.remove_card(args.deck, args.id):
        print(f"  🗑️  Removed card {args.id} from '{args.deck}'")
        return 0
    print(f"  ⚠️  Card {args.id} not found in '{args.deck}'")
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="srs",
        description="Spaced repetition flashcard study with SM-2 scheduling.",
    )
    sub = parser.add_subparsers(dest="command", help="Available commands")

    # create-deck
    p_cd = sub.add_parser("create-deck", help="Create a new deck")
    p_cd.add_argument("--name", required=True, help="Deck name")
    p_cd.set_defaults(func=cmd_create_deck)

    # decks
    p_decks = sub.add_parser("decks", help="List all decks")
    p_decks.set_defaults(func=cmd_decks)

    # add-card
    p_ac = sub.add_parser("add-card", help="Add a card to a deck")
    p_ac.add_argument("--deck", required=True, help="Deck name")
    p_ac.add_argument("--front", required=True, help="Front of card (question)")
    p_ac.add_argument("--back", required=True, help="Back of card (answer)")
    p_ac.add_argument("--tags", default="", help="Comma-separated tags")
    p_ac.set_defaults(func=cmd_add_card)

    # list-cards
    p_lc = sub.add_parser("list-cards", help="List cards in a deck")
    p_lc.add_argument("--deck", required=True, help="Deck name")
    p_lc.set_defaults(func=cmd_list_cards)

    # study
    p_study = sub.add_parser("study", help="Study due cards in a deck")
    p_study.add_argument("--deck", required=True, help="Deck name")
    p_study.set_defaults(func=cmd_study)

    # stats
    p_stats = sub.add_parser("stats", help="Show deck statistics")
    p_stats.add_argument("--deck", required=True, help="Deck name")
    p_stats.set_defaults(func=cmd_stats)

    # sample
    p_sample = sub.add_parser("sample", help="Load a sample deck")
    p_sample.set_defaults(func=cmd_sample)

    # delete-card
    p_dc = sub.add_parser("delete-card", help="Delete a card by ID")
    p_dc.add_argument("--deck", required=True, help="Deck name")
    p_dc.add_argument("id", type=int, help="Card ID")
    p_dc.set_defaults(func=cmd_delete_card)

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.command:
        print(WELCOME)
        parser.print_help()
        return 0

    engine = SRSEngine()
    try:
        return args.func(args, engine)
    except ValueError as exc:
        print(f"  ❌ Error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
