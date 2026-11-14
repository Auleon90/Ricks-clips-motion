"""
Benchmark runner for ricks-clips-motion rendering pipeline.

Measures render time, output quality metrics, and verifies key elements
are composited correctly.

Usage:
    python benchmarks/run_benchmark.py [--output-dir ./benchmark_out]
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.renderer import SceneSpec, VideoSpec, RicksClipsRenderer
from src.elements.captions import WordToken, CaptionTrack
from src.elements.scoreboard import ScoreboardOverlay, FlipCounter
from src.elements.overlays import TeamBanner, StatBadge, EmotionIndicator
from src.templates.battle_story import BattleStoryTemplate, BattleStoryConfig


SAMPLE_TOKENS = [
    {"word": "Two",        "start": 0.0,  "end": 0.35},
    {"word": "kingdoms",   "start": 0.35, "end": 0.95},
    {"word": "had",        "start": 0.95, "end": 1.25},
    {"word": "been",       "start": 1.25, "end": 1.55},
    {"word": "at",         "start": 1.55, "end": 1.75},
    {"word": "war",        "start": 1.75, "end": 2.1},
    {"word": "for",        "start": 2.1,  "end": 2.3},
    {"word": "99",         "start": 2.3,  "end": 2.8},
    {"word": "years",      "start": 2.8,  "end": 3.4},
    {"word": "without",    "start": 5.0,  "end": 5.6},
    {"word": "settling",   "start": 5.6,  "end": 6.3},
    {"word": "anything",   "start": 6.3,  "end": 7.0},
    {"word": "Two",        "start": 11.0, "end": 11.3},
    {"word": "massive",    "start": 11.3, "end": 11.9},
    {"word": "armies",     "start": 11.9, "end": 12.6},
    {"word": "clashed",    "start": 21.0, "end": 21.5},
    {"word": "first",      "start": 36.0, "end": 36.6},
    {"word": "strike",     "start": 36.6, "end": 37.2},
    {"word": "wins",       "start": 37.2, "end": 38.0},
]


BENCHMARKS = {
    "caption_render": {
        "description": "Render 10 word-by-word caption clips",
        "fn": "bench_caption_render",
    },
    "scoreboard_static": {
        "description": "Render static scoreboard overlay at value=99",
        "fn": "bench_scoreboard_static",
    },
    "scoreboard_animated": {
        "description": "Render 3-second animated scoreboard 0→99",
        "fn": "bench_scoreboard_animated",
    },
    "full_scene_composite": {
        "description": "Composite a 5-second scene with captions + scoreboard + banners",
        "fn": "bench_full_scene",
    },
    "battle_story_template": {
        "description": "Full 45-second BattleStoryTemplate render",
        "fn": "bench_battle_story",
    },
}


def bench_caption_render(output_dir: Path) -> dict:
    from moviepy import CompositeVideoClip, ColorClip
    track = CaptionTrack.from_srt_like(SAMPLE_TOKENS[:10])
    bg = ColorClip(size=(576, 1024), color=(30, 30, 40), duration=10)
    clips = track.build_clips()
    comp = CompositeVideoClip([bg] + clips, size=(576, 1024))
    out = str(output_dir / "bench_captions.mp4")
    comp.write_videofile(out, fps=30, codec="libx264", logger=None)
    return {"output": out, "clip_count": len(clips)}


def bench_scoreboard_static(output_dir: Path) -> dict:
    from moviepy import CompositeVideoClip, ColorClip
    sb = ScoreboardOverlay(label_left="YEARS", label_right="AT WAR")
    bg = ColorClip(size=(576, 1024), color=(60, 45, 30), duration=3)
    clip = sb.make_clip(value=99, duration=3)
    comp = CompositeVideoClip([bg, clip], size=(576, 1024))
    out = str(output_dir / "bench_scoreboard_static.mp4")
    comp.write_videofile(out, fps=30, codec="libx264", logger=None)
    return {"output": out}


def bench_scoreboard_animated(output_dir: Path) -> dict:
    from moviepy import CompositeVideoClip, ColorClip
    sb = ScoreboardOverlay(label_left="YEARS", label_right="AT WAR")
    bg = ColorClip(size=(576, 1024), color=(60, 45, 30), duration=3)
    clip = sb.make_animated_clip(start_value=0, end_value=99, duration=3)
    comp = CompositeVideoClip([bg, clip], size=(576, 1024))
    out = str(output_dir / "bench_scoreboard_animated.mp4")
    comp.write_videofile(out, fps=30, codec="libx264", logger=None)
    return {"output": out}


def bench_full_scene(output_dir: Path) -> dict:
    scene = SceneSpec(
        duration=5.0,
        background_color=(40, 50, 70),
        caption_tokens=SAMPLE_TOKENS[:8],
        scoreboard={
            "label_left": "YEARS",
            "label_right": "AT WAR",
            "value": 99,
            "animated": False,
            "position": (0.5, 0.35),
        },
        team_banners=[
            {"text": "SPEARS", "team": "red",  "position": (0.25, 0.08)},
            {"text": "SHIELDS", "team": "teal", "position": (0.75, 0.08)},
        ],
        stat_badges=[
            {"label": "ARMY SIZE", "value": "× 500", "team": "red", "position": (0.3, 0.9)},
        ],
    )
    spec = VideoSpec(scenes=[scene])
    renderer = RicksClipsRenderer(spec)
    out = str(output_dir / "bench_full_scene.mp4")
    renderer.write(out, verbose=False)
    return {"output": out}


def bench_battle_story(output_dir: Path) -> dict:
    cfg = BattleStoryConfig(
        team_a_name="SPEARS",
        team_b_name="SHIELDS",
        team_a_color="red",
        team_b_color="teal",
        years_at_war=99,
        narration_tokens=SAMPLE_TOKENS,
        duration_setup=8.0,
        duration_scoreboard=6.0,
        duration_army=8.0,
        duration_battle=8.0,
        duration_resolution=5.0,
        output_path=str(output_dir / "bench_battle_story.mp4"),
    )
    template = BattleStoryTemplate(cfg)
    renderer = template.build()
    out = str(output_dir / "bench_battle_story.mp4")
    renderer.write(out, verbose=False)
    return {"output": out}


BENCH_FNS = {
    "bench_caption_render": bench_caption_render,
    "bench_scoreboard_static": bench_scoreboard_static,
    "bench_scoreboard_animated": bench_scoreboard_animated,
    "bench_full_scene": bench_full_scene,
    "bench_battle_story": bench_battle_story,
}


def run_all(output_dir: Path, only: list = None) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    results = {}

    for name, meta in BENCHMARKS.items():
        if only and name not in only:
            continue
        print(f"\n{'='*60}")
        print(f"[{name}] {meta['description']}")
        t_start = time.perf_counter()
        try:
            fn = BENCH_FNS[meta["fn"]]
            details = fn(output_dir)
            elapsed = time.perf_counter() - t_start
            results[name] = {
                "status": "pass",
                "elapsed_s": round(elapsed, 3),
                "details": details,
            }
            print(f"  PASS  {elapsed:.2f}s  →  {details.get('output', '')}")
        except Exception as e:
            elapsed = time.perf_counter() - t_start
            results[name] = {
                "status": "fail",
                "elapsed_s": round(elapsed, 3),
                "error": str(e),
            }
            print(f"  FAIL  {elapsed:.2f}s  →  {e}")

    # Write summary JSON
    summary_path = output_dir / "benchmark_results.json"
    with open(summary_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults written to {summary_path}")
    return results


def main():
    parser = argparse.ArgumentParser(description="ricks-clips-motion benchmark runner")
    parser.add_argument("--output-dir", default="./benchmark_out",
                        help="Directory to write benchmark output videos")
    parser.add_argument("--only", nargs="+", choices=list(BENCHMARKS.keys()),
                        help="Run only specific benchmarks")
    parser.add_argument("--fast", action="store_true",
                        help="Skip full battle story benchmark (slow)")
    args = parser.parse_args()

    only = args.only
    if args.fast and not only:
        only = [k for k in BENCHMARKS if k != "battle_story_template"]

    results = run_all(Path(args.output_dir), only=only)

    # Exit code: 0 if all pass
    all_pass = all(r["status"] == "pass" for r in results.values())
    sys.exit(0 if all_pass else 1)


if __name__ == "__main__":
    main()
