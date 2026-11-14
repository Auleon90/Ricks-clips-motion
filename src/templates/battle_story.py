"""
BattleStoryTemplate — high-level template for Rick's Clips-style battle narrative videos.

Mirrors the structure observed in the reference video:
  Scene 1: Setup (characters, shop, exposition captions)
  Scene 2: Scoreboard reveal (years at war counter)
  Scene 3: Army formation aerial shot
  Scene 4: Battle / confrontation close-up
  Scene 5: Resolution / outcome
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Tuple
import numpy as np
from moviepy import ColorClip

from ..renderer import SceneSpec, VideoSpec, RicksClipsRenderer


@dataclass
class BattleStoryConfig:
    """Declarative configuration for a BattleStoryTemplate render."""

    # Teams
    team_a_name: str = "RED"
    team_b_name: str = "TEAL"
    team_a_color: str = "red"
    team_b_color: str = "teal"

    # Story narration — list of dicts {word, start, end}
    # Each scene gets a slice of the full token list
    narration_tokens: List[dict] = field(default_factory=list)

    # Years-at-war scoreboard
    years_at_war: int = 99
    show_scoreboard_at: float = 5.0     # seconds from video start

    # Optional background clips per scene (None = solid color)
    bg_scene_1: Optional[object] = None   # setup scene
    bg_scene_2: Optional[object] = None   # scoreboard scene
    bg_scene_3: Optional[object] = None   # army formation
    bg_scene_4: Optional[object] = None   # battle
    bg_scene_5: Optional[object] = None   # resolution

    # Scene durations (seconds)
    duration_setup: float = 10.0
    duration_scoreboard: float = 8.0
    duration_army: float = 10.0
    duration_battle: float = 10.0
    duration_resolution: float = 7.0

    # Audio
    audio_path: Optional[str] = None

    # Output
    output_path: str = "output.mp4"
    output_size: Tuple[int, int] = (576, 1024)


# Default background gradients (solid colors if no clip provided)
_BG_SETUP = (45, 50, 70)
_BG_SCOREBOARD = (60, 45, 30)
_BG_ARMY = (40, 70, 40)
_BG_BATTLE = (70, 40, 40)
_BG_RESOLUTION = (40, 60, 70)


def _tokens_in_window(tokens: List[dict], t_start: float, t_end: float) -> List[dict]:
    """Filter tokens to those that overlap [t_start, t_end], offset to scene-local time."""
    result = []
    for tok in tokens:
        if tok["end"] <= t_start or tok["start"] >= t_end:
            continue
        result.append({
            "word": tok["word"],
            "start": max(tok["start"] - t_start, 0.0),
            "end": min(tok["end"] - t_start, t_end - t_start),
        })
    return result


class BattleStoryTemplate:
    """
    Builds a full VideoSpec from a BattleStoryConfig.

    Example usage:
        config = BattleStoryConfig(
            team_a_name="SPEARS",
            team_b_name="SHIELDS",
            years_at_war=99,
            narration_tokens=[
                {"word": "Two", "start": 0.0, "end": 0.4},
                {"word": "kingdoms", "start": 0.4, "end": 1.0},
                ...
            ],
        )
        template = BattleStoryTemplate(config)
        renderer = template.build()
        renderer.write("battle.mp4")
    """

    def __init__(self, config: BattleStoryConfig):
        self.cfg = config

    def _make_color_bg(self, color: tuple, duration: float):
        return ColorClip(size=self.cfg.output_size, color=color, duration=duration)

    def build(self) -> RicksClipsRenderer:
        cfg = self.cfg
        w, h = cfg.output_size

        # Cumulative time offsets
        t0 = 0.0
        t1 = t0 + cfg.duration_setup
        t2 = t1 + cfg.duration_scoreboard
        t3 = t2 + cfg.duration_army
        t4 = t3 + cfg.duration_battle
        t5 = t4 + cfg.duration_resolution

        # --- Scene 1: Setup ---
        scene1 = SceneSpec(
            duration=cfg.duration_setup,
            background_clip=cfg.bg_scene_1 or self._make_color_bg(_BG_SETUP, cfg.duration_setup),
            caption_tokens=_tokens_in_window(cfg.narration_tokens, t0, t1),
            team_banners=[
                {"text": cfg.team_a_name, "team": cfg.team_a_color,
                 "position": (0.25, 0.08)},
                {"text": cfg.team_b_name, "team": cfg.team_b_color,
                 "position": (0.75, 0.08)},
            ],
        )

        # --- Scene 2: Scoreboard ---
        scene2 = SceneSpec(
            duration=cfg.duration_scoreboard,
            background_clip=cfg.bg_scene_2 or self._make_color_bg(_BG_SCOREBOARD, cfg.duration_scoreboard),
            caption_tokens=_tokens_in_window(cfg.narration_tokens, t1, t2),
            scoreboard={
                "label_left": "YEARS",
                "label_right": "AT WAR",
                "value": cfg.years_at_war,
                "animated": True,
                "start_val": 0,
                "position": (0.5, 0.42),
            },
        )

        # --- Scene 3: Army formation ---
        scene3 = SceneSpec(
            duration=cfg.duration_army,
            background_clip=cfg.bg_scene_3 or self._make_color_bg(_BG_ARMY, cfg.duration_army),
            caption_tokens=_tokens_in_window(cfg.narration_tokens, t2, t3),
            stat_badges=[
                {"label": cfg.team_a_name, "value": "× 500",
                 "team": cfg.team_a_color, "position": (0.25, 0.9)},
                {"label": cfg.team_b_name, "value": "× 500",
                 "team": cfg.team_b_color, "position": (0.75, 0.9)},
            ],
        )

        # --- Scene 4: Battle ---
        scene4 = SceneSpec(
            duration=cfg.duration_battle,
            background_clip=cfg.bg_scene_4 or self._make_color_bg(_BG_BATTLE, cfg.duration_battle),
            caption_tokens=_tokens_in_window(cfg.narration_tokens, t3, t4),
            emotion_indicators=[
                {"emotion": "sweat", "position": (0.3, 0.35), "start": 0.5, "duration": 2.0},
                {"emotion": "shock", "position": (0.7, 0.35), "start": 1.0, "duration": 2.0},
            ],
            team_banners=[
                {"text": "VS", "team": "gold", "position": (0.5, 0.5)},
            ],
        )

        # --- Scene 5: Resolution ---
        scene5 = SceneSpec(
            duration=cfg.duration_resolution,
            background_clip=cfg.bg_scene_5 or self._make_color_bg(_BG_RESOLUTION, cfg.duration_resolution),
            caption_tokens=_tokens_in_window(cfg.narration_tokens, t4, t5),
        )

        spec = VideoSpec(
            scenes=[scene1, scene2, scene3, scene4, scene5],
            audio_path=cfg.audio_path,
            output_size=cfg.output_size,
            output_fps=30,
            transition="zoom",
            transition_duration=0.2,
        )
        return RicksClipsRenderer(spec)
