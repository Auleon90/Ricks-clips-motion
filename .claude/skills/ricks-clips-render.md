# ricks-clips-render

Skill for rendering Rick's Clips-style motion graphics videos using the `ricks-clips-motion` pipeline.

## When to use
Invoke this skill whenever asked to:
- Render a battle/story narration video in Rick's Clips style
- Add word-by-word captions to a video
- Create a scoreboard / flip-counter overlay
- Composite team banners, stat badges, or emotion indicators
- Run the benchmark suite

## Style reference
Derived from Rick's Clips visual language:
- **Format**: 9:16 vertical, 576×1024, 30 fps
- **Captions**: white bold text, thick black stroke, word-by-word at 78% height
- **Teams**: Red (#C01E2D) vs Teal (#009688) with gold (#D4AF37) for neutral
- **Scoreboard**: Wooden board with two-color split label + 3-digit flip counter
- **Characters**: Circular-head stickmen, expressive emotions (sweat/shock/happy)
- **Transitions**: Zoom punch-in between scenes (0.2s), fade for gentler cuts

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
        # ... full token list
    ],
)
renderer = BattleStoryTemplate(cfg).build()
renderer.write("output.mp4")
```

## Module reference

| Module | Purpose |
|--------|---------|
| `src.renderer` | `RicksClipsRenderer`, `SceneSpec`, `VideoSpec` — core compositor |
| `src.elements.captions` | `CaptionTrack`, `WordToken` — word-by-word subtitle system |
| `src.elements.scoreboard` | `ScoreboardOverlay`, `FlipCounter` — animated counter board |
| `src.elements.overlays` | `TeamBanner`, `StatBadge`, `EmotionIndicator` |
| `src.elements.transitions` | `FadeTransition`, `SlideTransition`, `ZoomTransition` |
| `src.templates.battle_story` | `BattleStoryTemplate` — full 5-scene story template |

## Running benchmarks

```bash
# Fast subset (skips full 45s render)
python benchmarks/run_benchmark.py --fast

# All benchmarks
python benchmarks/run_benchmark.py --output-dir ./benchmark_out

# Specific benchmark
python benchmarks/run_benchmark.py --only caption_render scoreboard_animated
```

Results written to `benchmark_out/benchmark_results.json`.

## Adding a new scene type

1. Create a `SceneSpec` with your layers:
```python
from src.renderer import SceneSpec, VideoSpec, RicksClipsRenderer

scene = SceneSpec(
    duration=10.0,
    background_clip=your_moviepy_clip,   # or background_color=(r,g,b)
    caption_tokens=[...],
    scoreboard={"label_left": "GOLD", "label_right": "COINS", "value": 500},
    team_banners=[{"text": "WINNER", "team": "gold", "position": (0.5, 0.1)}],
)
renderer = RicksClipsRenderer(VideoSpec(scenes=[scene]))
renderer.write("scene.mp4")
```

## Color palette

```
Red team:   fill #C01E2D   border #8C141E   text #FFFFFF
Teal team:  fill #009688   border #006E64   text #FFFFFF
Gold:       fill #D4AF37   border #A08214   text #281400
Wood board: bg   #65432B   border #8B5A2B
Digit card: bg   #F5F0DC   text   #141414
```
