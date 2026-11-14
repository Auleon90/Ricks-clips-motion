"""
Demo: render a sample Rick's Clips-style battle story video.

Run:
    python examples/demo_battle.py --output demo_battle.mp4
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import argparse
from src.templates.battle_story import BattleStoryTemplate, BattleStoryConfig

NARRATION = [
    {"word": "Two",        "start": 0.3,  "end": 0.65},
    {"word": "kingdoms",   "start": 0.65, "end": 1.3},
    {"word": "couldn't",   "start": 1.3,  "end": 1.75},
    {"word": "settle",     "start": 1.75, "end": 2.2},
    {"word": "anything",   "start": 2.2,  "end": 2.9},
    {"word": "for",        "start": 5.1,  "end": 5.4},
    {"word": "99",         "start": 5.4,  "end": 5.9},
    {"word": "years",      "start": 5.9,  "end": 6.6},
    {"word": "at",         "start": 6.6,  "end": 6.9},
    {"word": "war",        "start": 6.9,  "end": 7.5},
    {"word": "Two",        "start": 14.2, "end": 14.5},
    {"word": "massive",    "start": 14.5, "end": 15.1},
    {"word": "armies",     "start": 15.1, "end": 15.9},
    {"word": "clashed",    "start": 24.5, "end": 25.1},
    {"word": "first",      "start": 36.0, "end": 36.6},
    {"word": "strike",     "start": 36.6, "end": 37.2},
    {"word": "wins",       "start": 37.2, "end": 38.0},
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="demo_battle.mp4")
    args = parser.parse_args()

    cfg = BattleStoryConfig(
        team_a_name="SPEARS",
        team_b_name="SHIELDS",
        team_a_color="red",
        team_b_color="teal",
        years_at_war=99,
        narration_tokens=NARRATION,
        duration_setup=8.0,
        duration_scoreboard=6.0,
        duration_army=8.0,
        duration_battle=8.0,
        duration_resolution=5.0,
        output_path=args.output,
    )

    print(f"Rendering Rick's Clips battle story → {args.output}")
    template = BattleStoryTemplate(cfg)
    renderer = template.build()
    renderer.write(args.output, verbose=True)
    print(f"Done! {args.output}")


if __name__ == "__main__":
    main()
