# ricks-clips-motion

Motion graphics rendering pipeline for **Rick's Clips**-style vertical storytelling videos.

Derived from visual analysis of a reference Rick's Clips video:
- 9:16 vertical format (576 × 1024, 30 fps)
- Word-by-word subtitle captions
- Animated flip-counter scoreboard ("YEARS AT WAR")
- Two-team color system (Red vs Teal)
- Stickman character close-ups with emotion overlays
- Aerial army formation shots
- Zoom punch-in transitions

---

## Install

```bash
pip install -r requirements.txt
```

Requires `ffmpeg` on `$PATH` (pre-installed in the cloud container).

---

## Quick start

```python
from src.templates.battle_story import BattleStoryTemplate, BattleStoryConfig

cfg = BattleStoryConfig(
    team_a_name="SPEARS",
    team_b_name="SHIELDS",
    years_at_war=99,
    narration_tokens=[
        {"word": "Two",      "start": 0.0, "end": 0.4},
        {"word": "kingdoms", "start": 0.4, "end": 1.0},
        {"word": "clashed",  "start": 1.0, "end": 1.6},
    ],
    duration_setup=10.0,
    duration_scoreboard=8.0,
    duration_army=10.0,
    duration_battle=10.0,
    duration_resolution=7.0,
)

renderer = BattleStoryTemplate(cfg).build()
renderer.write("battle.mp4", verbose=True)
```

Or run the included demo:

```bash
python examples/demo_battle.py --output demo_battle.mp4
```

---

## Benchmark

```bash
# Fast (skips full video render)
python benchmarks/run_benchmark.py --fast --output-dir ./benchmark_out

# Full suite
python benchmarks/run_benchmark.py --output-dir ./benchmark_out
```

Results in `benchmark_out/benchmark_results.json`:

```json
{
  "caption_render":        {"status": "pass", "elapsed_s": 4.2, ...},
  "scoreboard_static":     {"status": "pass", "elapsed_s": 1.8, ...},
  "scoreboard_animated":   {"status": "pass", "elapsed_s": 3.1, ...},
  "full_scene_composite":  {"status": "pass", "elapsed_s": 7.4, ...},
  "battle_story_template": {"status": "pass", "elapsed_s": 55.2, ...}
}
```

---

## Project structure

```
ricks-clips-motion/
├── src/
│   ├── renderer.py              Core compositor (SceneSpec, VideoSpec, RicksClipsRenderer)
│   └── elements/
│       ├── captions.py          Word-by-word caption system
│       ├── scoreboard.py        Flip-counter scoreboard overlay
│       ├── transitions.py       Fade / Slide / Zoom transitions
│       └── overlays.py          Team banners, stat badges, emotion indicators
│   └── templates/
│       └── battle_story.py      5-scene battle story high-level template
├── benchmarks/
│   └── run_benchmark.py         Benchmark runner + timing results
├── examples/
│   └── demo_battle.py           Runnable demo
├── .claude/
│   └── skills/
│       └── ricks-clips-render.md  Claude Code skill
└── requirements.txt
```

---

## Visual style reference

| Element | Spec |
|---------|------|
| Resolution | 576 × 1024 (9:16) |
| Frame rate | 30 fps |
| Caption font | Bold sans-serif, 52px |
| Caption stroke | Black, 4px |
| Caption Y-pos | 78% from top |
| Red team | `#C01E2D` |
| Teal team | `#009688` |
| Gold / neutral | `#D4AF37` |
| Board wood | `#65432B` |
| Digit card | `#F5F0DC` |
| Transition | Zoom punch-in 0.2s |

---

## License

MIT
