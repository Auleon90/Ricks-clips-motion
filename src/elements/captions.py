"""Word-by-word caption system matching Rick's Clips subtitle style."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy import ImageClip, CompositeVideoClip


# Style constants derived from visual analysis of reference video
CAPTION_FONT_SIZE = 52
CAPTION_COLOR = (255, 255, 255)        # white fill
CAPTION_STROKE_COLOR = (0, 0, 0)       # black stroke
CAPTION_STROKE_WIDTH = 4
CAPTION_Y_POSITION = 0.78              # 78% from top (bottom area)
CAPTION_SHADOW_OFFSET = (3, 3)
CAPTION_SHADOW_COLOR = (0, 0, 0, 160)


@dataclass
class WordToken:
    text: str
    start: float    # seconds
    end: float      # seconds


@dataclass
class CaptionFrame:
    """A single caption display window (one or two words highlighted)."""
    words: List[WordToken]
    start: float
    end: float
    highlight_index: int = 0


class WordByWordCaption:
    """
    Renders word-by-word captions in Rick's Clips style:
    - Bold white text with thick black stroke
    - Centered horizontally
    - Positioned in lower third
    - Current word slightly larger / brighter
    """

    def __init__(
        self,
        video_size: tuple[int, int] = (576, 1024),
        font_path: Optional[str] = None,
        font_size: int = CAPTION_FONT_SIZE,
        y_position: float = CAPTION_Y_POSITION,
    ):
        self.w, self.h = video_size
        self.font_size = font_size
        self.y_position = y_position
        self._font = self._load_font(font_path, font_size)
        self._font_sm = self._load_font(font_path, int(font_size * 0.9))

    def _load_font(self, path: Optional[str], size: int) -> ImageFont.FreeTypeFont:
        if path:
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                pass
        # Try system fonts in order of preference
        candidates = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "/usr/share/fonts/truetype/ubuntu/Ubuntu-B.ttf",
            "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
        ]
        for c in candidates:
            try:
                return ImageFont.truetype(c, size)
            except OSError:
                continue
        return ImageFont.load_default()

    def _render_word(self, text: str, font: ImageFont.FreeTypeFont) -> Image.Image:
        """Render a single word with stroke + fill onto a transparent image."""
        dummy = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
        bbox = dummy.textbbox((0, 0), text, font=font)
        sw = CAPTION_STROKE_WIDTH
        w = bbox[2] - bbox[0] + sw * 2 + 6
        h = bbox[3] - bbox[1] + sw * 2 + 6
        img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        x, y = sw + 3 - bbox[0], sw + 3 - bbox[1]
        # Stroke (draw text shifted in 8 directions)
        for dx in range(-sw, sw + 1):
            for dy in range(-sw, sw + 1):
                if dx == 0 and dy == 0:
                    continue
                draw.text((x + dx, y + dy), text, font=font, fill=CAPTION_STROKE_COLOR)
        # Shadow
        draw.text(
            (x + CAPTION_SHADOW_OFFSET[0], y + CAPTION_SHADOW_OFFSET[1]),
            text, font=font, fill=CAPTION_SHADOW_COLOR,
        )
        # Fill
        draw.text((x, y), text, font=font, fill=CAPTION_COLOR)
        return img

    def make_clip(self, token: WordToken, duration: Optional[float] = None) -> ImageClip:
        """Create a MoviePy ImageClip for a single word token."""
        dur = duration if duration is not None else (token.end - token.start)
        word_img = self._render_word(token.text, self._font)
        ww, wh = word_img.size
        # Composite onto transparent canvas sized to video
        canvas = Image.new("RGBA", (self.w, self.h), (0, 0, 0, 0))
        x = (self.w - ww) // 2
        y = int(self.h * self.y_position)
        canvas.paste(word_img, (x, y), word_img)
        arr = np.array(canvas)
        clip = ImageClip(arr, duration=dur).with_start(token.start)
        return clip


class CaptionTrack:
    """
    Manages a full caption track from a list of timed words.
    Produces a list of MoviePy clips to overlay on the video.
    """

    def __init__(
        self,
        tokens: List[WordToken],
        video_size: tuple[int, int] = (576, 1024),
        font_path: Optional[str] = None,
    ):
        self.tokens = tokens
        self.renderer = WordByWordCaption(video_size=video_size, font_path=font_path)

    @classmethod
    def from_srt_like(cls, entries: List[dict], **kwargs) -> "CaptionTrack":
        """
        Build from list of dicts: [{"word": "hello", "start": 0.0, "end": 0.5}, ...]
        """
        tokens = [WordToken(e["word"], e["start"], e["end"]) for e in entries]
        return cls(tokens, **kwargs)

    def build_clips(self) -> List[ImageClip]:
        return [self.renderer.make_clip(t) for t in self.tokens]

    def overlay_on(self, base_clip) -> CompositeVideoClip:
        """Return a CompositeVideoClip with captions on top of base_clip."""
        caption_clips = self.build_clips()
        return CompositeVideoClip([base_clip] + caption_clips)
