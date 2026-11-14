"""Scene transition effects matching Rick's Clips editing style."""

from __future__ import annotations
from typing import Optional
import numpy as np
from moviepy import VideoClip, CompositeVideoClip, concatenate_videoclips


def _ease_in_out(t: float) -> float:
    """Smooth step."""
    return t * t * (3 - 2 * t)


class FadeTransition:
    """
    Cross-fade between two clips over a given duration.
    clip_a fades out, clip_b fades in simultaneously.
    """

    def __init__(self, duration: float = 0.3):
        self.duration = duration

    def apply(self, clip_a, clip_b) -> CompositeVideoClip:
        d = self.duration
        a = clip_a.with_effects([])  # keep original
        b = clip_b.with_start(clip_a.duration - d)

        # Apply cross-fade using audio_fadein/out style approach
        a_faded = a.with_end(clip_a.duration)
        # Manual fade-out on a
        def apply_fade(frame, t):
            overlap_start = clip_a.duration - d
            if t >= overlap_start:
                alpha = 1.0 - _ease_in_out((t - overlap_start) / d)
                return (frame * alpha).astype(np.uint8)
            return frame

        b_faded = b
        result = CompositeVideoClip([a_faded, b_faded])
        return result


class SlideTransition:
    """
    Slide clip_b in from a direction while clip_a slides out.
    direction: 'left', 'right', 'up', 'down'
    """

    def __init__(self, duration: float = 0.4, direction: str = "left"):
        self.duration = duration
        self.direction = direction

    def apply(self, clip_a, clip_b):
        d = self.duration
        w, h = clip_a.size
        direction = self.direction

        def make_frame(t: float) -> np.ndarray:
            # t is relative to transition start
            p = _ease_in_out(min(t / d, 1.0))
            if direction == "left":
                dx_a = -int(w * p)
                dx_b = int(w * (1 - p))
                dy = 0
            elif direction == "right":
                dx_a = int(w * p)
                dx_b = -int(w * (1 - p))
                dy = 0
            elif direction == "up":
                dx_a, dx_b = 0, 0
                dy_a = -int(h * p)
                dy_b = int(h * (1 - p))
            else:  # down
                dx_a, dx_b = 0, 0
                dy_a = int(h * p)
                dy_b = -int(h * (1 - p))

            frame_a = clip_a.get_frame(clip_a.duration - d + t)
            frame_b = clip_b.get_frame(t)
            canvas = np.zeros((h, w, 3), dtype=np.uint8)

            # Place clip_a
            if direction in ("left", "right"):
                dy_a = dy_b = 0
            xa_start = max(dx_a, 0)
            xa_src_start = max(-dx_a, 0)
            xa_width = w - abs(dx_a)
            if xa_width > 0:
                canvas[dy_a: dy_a + h, xa_start: xa_start + xa_width] = \
                    frame_a[0:h, xa_src_start: xa_src_start + xa_width]

            xb_start = max(dx_b, 0)
            xb_src_start = max(-dx_b, 0)
            xb_width = w - abs(dx_b)
            if xb_width > 0:
                canvas[dy_b: dy_b + h, xb_start: xb_start + xb_width] = \
                    frame_b[0:h, xb_src_start: xb_src_start + xb_width]

            return canvas

        transition = VideoClip(make_frame, duration=d)
        pre = clip_a.subclipped(0, clip_a.duration - d) if clip_a.duration > d else clip_a
        post = clip_b.subclipped(d) if clip_b.duration > d else clip_b
        return concatenate_videoclips([pre, transition, post])


class ZoomTransition:
    """
    Zoom punch-in transition: quick scale-up between clips (Rick's Clips action cut).
    """

    def __init__(self, duration: float = 0.2, scale_max: float = 1.3):
        self.duration = duration
        self.scale_max = scale_max

    def apply(self, clip_a, clip_b):
        from moviepy.video.fx import Resize
        d = self.duration

        def zoom_out_frame(get_frame, t):
            frame = get_frame(t)
            h, w = frame.shape[:2]
            # ease scale from scale_max → 1.0
            p = _ease_in_out(t / d)
            scale = self.scale_max - (self.scale_max - 1.0) * p
            new_w = int(w * scale)
            new_h = int(h * scale)
            from PIL import Image
            img = Image.fromarray(frame).resize((new_w, new_h), Image.LANCZOS)
            # Center crop back to original size
            x = (new_w - w) // 2
            y = (new_h - h) // 2
            return np.array(img)[y:y + h, x:x + w]

        transition_part = clip_b.subclipped(0, d)
        transition = transition_part.transform(zoom_out_frame)
        pre = clip_a
        post = clip_b.subclipped(d) if clip_b.duration > d else clip_b
        return concatenate_videoclips([pre, transition, post])
