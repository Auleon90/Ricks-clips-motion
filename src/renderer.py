"""
Core renderer: composes a full Rick's Clips-style motion graphics video
from a scene spec dict or a SceneSpec dataclass.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import numpy as np
from PIL import Image, ImageDraw
from moviepy import (
    VideoFileClip, ImageClip, ColorClip, CompositeVideoClip,
    concatenate_videoclips, AudioFileClip,
)

from .elements.captions import WordToken, CaptionTrack
from .elements.scoreboard import ScoreboardOverlay
from .elements.overlays import TeamBanner, StatBadge, EmotionIndicator
from .elements.transitions import FadeTransition, ZoomTransition, SlideTransition


# Canonical output format matching reference video
OUTPUT_SIZE = (576, 1024)   # 9:16 vertical
OUTPUT_FPS = 30


@dataclass
class SceneSpec:
    """
    Specification for a single scene segment.
    Maps directly to compositing layers.
    """
    duration: float
    background_color: tuple = (20, 20, 30)   # fallback if no video clip
    background_clip: Optional[Any] = None    # MoviePy clip
    caption_tokens: List[dict] = field(default_factory=list)
    scoreboard: Optional[dict] = None        # {label_left, label_right, value, animated, start_val}
    team_banners: List[dict] = field(default_factory=list)
    stat_badges: List[dict] = field(default_factory=list)
    emotion_indicators: List[dict] = field(default_factory=list)
    start_offset: float = 0.0               # for timeline positioning


@dataclass
class VideoSpec:
    """Full video specification."""
    scenes: List[SceneSpec]
    audio_path: Optional[str] = None
    output_fps: int = OUTPUT_FPS
    output_size: tuple = OUTPUT_SIZE
    transition: str = "fade"                # fade | slide | zoom | cut
    transition_duration: float = 0.25


class RicksClipsRenderer:
    """
    Builds a final CompositeVideoClip from a VideoSpec.

    Usage:
        spec = VideoSpec(scenes=[...])
        renderer = RicksClipsRenderer(spec)
        final_clip = renderer.render()
        final_clip.write_videofile("output.mp4", fps=30, codec="libx264")
    """

    def __init__(self, spec: VideoSpec):
        self.spec = spec
        self.w, self.h = spec.output_size

    def _build_scene_clip(self, scene: SceneSpec):
        layers = []

        # --- Background layer ---
        if scene.background_clip is not None:
            bg = scene.background_clip
            # Resize to output size if needed
            if bg.size != (self.w, self.h):
                bg = bg.resized((self.w, self.h))
            if bg.duration < scene.duration:
                bg = bg.with_end(scene.duration)
            bg = bg.subclipped(0, scene.duration)
        else:
            bg = ColorClip(size=(self.w, self.h),
                           color=scene.background_color,
                           duration=scene.duration)
        layers.append(bg)

        # --- Scoreboard ---
        if scene.scoreboard:
            sb_cfg = scene.scoreboard
            sb = ScoreboardOverlay(
                label_left=sb_cfg.get("label_left", "TEAM"),
                label_right=sb_cfg.get("label_right", "SCORE"),
                video_size=(self.w, self.h),
                position=sb_cfg.get("position", (0.5, 0.35)),
            )
            if sb_cfg.get("animated", False):
                layers.append(sb.make_animated_clip(
                    start_value=sb_cfg.get("start_val", 0),
                    end_value=sb_cfg.get("value", 0),
                    duration=scene.duration,
                ))
            else:
                layers.append(sb.make_clip(
                    value=sb_cfg.get("value", 0),
                    duration=scene.duration,
                ))

        # --- Team banners ---
        for banner_cfg in scene.team_banners:
            banner = TeamBanner(
                text=banner_cfg["text"],
                team=banner_cfg.get("team", "red"),
                video_size=(self.w, self.h),
                position=banner_cfg.get("position", (0.5, 0.1)),
            )
            layers.append(banner.make_clip(scene.duration))

        # --- Stat badges ---
        for badge_cfg in scene.stat_badges:
            badge = StatBadge(
                label=badge_cfg.get("label", ""),
                value=badge_cfg.get("value", ""),
                team=badge_cfg.get("team", "teal"),
                video_size=(self.w, self.h),
                position=badge_cfg.get("position", (0.5, 0.88)),
            )
            layers.append(badge.make_clip(scene.duration))

        # --- Emotion indicators ---
        for emo_cfg in scene.emotion_indicators:
            emo = EmotionIndicator(
                emotion=emo_cfg.get("emotion", "sweat"),
                video_size=(self.w, self.h),
                position=emo_cfg.get("position", (0.3, 0.4)),
            )
            start = emo_cfg.get("start", 0.0)
            dur = emo_cfg.get("duration", scene.duration - start)
            layers.append(emo.make_clip(dur, start=start))

        # --- Word-by-word captions ---
        if scene.caption_tokens:
            track = CaptionTrack.from_srt_like(
                scene.caption_tokens,
                video_size=(self.w, self.h),
            )
            layers.extend(track.build_clips())

        return CompositeVideoClip(layers, size=(self.w, self.h))

    def render(self):
        """Build and return the final composited MoviePy clip."""
        scene_clips = [self._build_scene_clip(s) for s in self.spec.scenes]

        # Apply transitions between scenes
        if len(scene_clips) == 1:
            final = scene_clips[0]
        else:
            t = self.spec.transition
            d = self.spec.transition_duration
            if t == "fade":
                trans = FadeTransition(d)
            elif t == "zoom":
                trans = ZoomTransition(d)
            elif t == "slide":
                trans = SlideTransition(d)
            else:
                trans = None

            if trans is None:
                final = concatenate_videoclips(scene_clips)
            else:
                # Apply pairwise
                result = scene_clips[0]
                for next_clip in scene_clips[1:]:
                    result = trans.apply(result, next_clip)
                final = result

        # Attach audio
        if self.spec.audio_path:
            audio = AudioFileClip(self.spec.audio_path)
            if audio.duration > final.duration:
                audio = audio.subclipped(0, final.duration)
            final = final.with_audio(audio)

        return final

    def write(
        self,
        output_path: str,
        fps: Optional[int] = None,
        codec: str = "libx264",
        audio_codec: str = "aac",
        preset: str = "medium",
        verbose: bool = False,
    ) -> str:
        fps = fps or self.spec.output_fps
        clip = self.render()
        clip.write_videofile(
            output_path,
            fps=fps,
            codec=codec,
            audio_codec=audio_codec,
            preset=preset,
            logger="bar" if verbose else None,
        )
        return output_path
