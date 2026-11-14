"""UI overlays: team banners, stat badges, emotion indicators."""

from __future__ import annotations
from typing import Tuple, Optional
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy import ImageClip


TEAM_COLORS = {
    "red":  {"fill": (192, 30, 45),  "border": (140, 20, 30),  "text": (255, 255, 255)},
    "teal": {"fill": (0, 150, 136),  "border": (0, 110, 100),  "text": (255, 255, 255)},
    "gold": {"fill": (212, 175, 55), "border": (160, 130, 20), "text": (40, 20, 0)},
}


def _load_font(size: int, bold: bool = True) -> ImageFont.FreeTypeFont:
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ]
    for c in candidates:
        try:
            return ImageFont.truetype(c, size)
        except OSError:
            continue
    return ImageFont.load_default()


class TeamBanner:
    """
    Horizontal team label banner (like 'SPEARS | SHIELDS' signage in reference).
    """

    def __init__(
        self,
        text: str,
        team: str = "red",
        width: int = 180,
        height: int = 44,
        video_size: Tuple[int, int] = (576, 1024),
        position: Tuple[float, float] = (0.5, 0.1),
    ):
        self.text = text
        self.team = team
        self.width = width
        self.height = height
        self.video_w, self.video_h = video_size
        self.pos_cx, self.pos_cy = position
        self.font = _load_font(24)

    def _render(self) -> Image.Image:
        colors = TEAM_COLORS.get(self.team, TEAM_COLORS["red"])
        img = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        # Rounded rect background
        draw.rounded_rectangle([0, 0, self.width - 1, self.height - 1],
                                radius=6, fill=colors["fill"],
                                outline=colors["border"], width=3)
        # Text
        bb = draw.textbbox((0, 0), self.text, font=self.font)
        tw = bb[2] - bb[0]
        th = bb[3] - bb[1]
        tx = (self.width - tw) // 2 - bb[0]
        ty = (self.height - th) // 2 - bb[1]
        draw.text((tx + 1, ty + 1), self.text, font=self.font, fill=(0, 0, 0, 100))
        draw.text((tx, ty), self.text, font=self.font, fill=colors["text"])
        return img

    def make_clip(self, duration: float, start: float = 0.0) -> ImageClip:
        banner = self._render()
        canvas = Image.new("RGBA", (self.video_w, self.video_h), (0, 0, 0, 0))
        bx = int(self.video_w * self.pos_cx) - self.width // 2
        by = int(self.video_h * self.pos_cy) - self.height // 2
        canvas.paste(banner, (bx, by), banner)
        return ImageClip(np.array(canvas), duration=duration).with_start(start)


class StatBadge:
    """
    Small stat pill: e.g. '× 500' army count badge, gold coin amount, etc.
    """

    def __init__(
        self,
        label: str,
        value: str,
        team: str = "teal",
        video_size: Tuple[int, int] = (576, 1024),
        position: Tuple[float, float] = (0.5, 0.9),
    ):
        self.label = label
        self.value = value
        self.team = team
        self.video_w, self.video_h = video_size
        self.pos_cx, self.pos_cy = position
        self.font_label = _load_font(18, bold=False)
        self.font_value = _load_font(26, bold=True)

    def _render(self) -> Image.Image:
        colors = TEAM_COLORS.get(self.team, TEAM_COLORS["teal"])
        # Measure
        dummy_draw = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
        lb = dummy_draw.textbbox((0, 0), self.label, font=self.font_label)
        vb = dummy_draw.textbbox((0, 0), self.value, font=self.font_value)
        pad = 12
        inner_w = max(lb[2] - lb[0], vb[2] - vb[0]) + pad * 2
        inner_h = (lb[3] - lb[1]) + (vb[3] - vb[1]) + pad * 2 + 4
        img = Image.new("RGBA", (inner_w, inner_h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.rounded_rectangle([0, 0, inner_w - 1, inner_h - 1],
                                radius=8, fill=colors["fill"],
                                outline=colors["border"], width=2)
        # Label
        lw = lb[2] - lb[0]
        draw.text(((inner_w - lw) // 2 - lb[0], pad - lb[1]),
                  self.label, font=self.font_label, fill=(*colors["text"][:3], 180))
        # Value
        vw = vb[2] - vb[0]
        draw.text(((inner_w - vw) // 2 - vb[0], pad + (lb[3] - lb[1]) + 4 - vb[1]),
                  self.value, font=self.font_value, fill=colors["text"])
        return img

    def make_clip(self, duration: float, start: float = 0.0) -> ImageClip:
        badge = self._render()
        canvas = Image.new("RGBA", (self.video_w, self.video_h), (0, 0, 0, 0))
        bw, bh = badge.size
        bx = int(self.video_w * self.pos_cx) - bw // 2
        by = int(self.video_h * self.pos_cy) - bh // 2
        canvas.paste(badge, (bx, by), badge)
        return ImageClip(np.array(canvas), duration=duration).with_start(start)


class EmotionIndicator:
    """
    Sweat-drop / exclamation emoji overlay above character position.
    Rendered as simple geometric emoji-style icons.
    """

    EMOTIONS = {
        "sweat": "💧",
        "shock": "!!",
        "happy": "★",
        "angry": "⚡",
        "money": "$",
    }

    def __init__(
        self,
        emotion: str = "sweat",
        video_size: Tuple[int, int] = (576, 1024),
        position: Tuple[float, float] = (0.3, 0.4),
        size: int = 48,
    ):
        self.emotion = emotion
        self.video_w, self.video_h = video_size
        self.pos_cx, self.pos_cy = position
        self.size = size
        self.font = _load_font(size)

    def _render(self) -> Image.Image:
        symbol = self.EMOTIONS.get(self.emotion, self.emotion)
        img = Image.new("RGBA", (self.size * 2, self.size * 2), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.text((2, 2), symbol, font=self.font, fill=(0, 0, 0, 160))
        draw.text((0, 0), symbol, font=self.font, fill=(255, 255, 255, 230))
        return img

    def make_clip(self, duration: float, start: float = 0.0) -> ImageClip:
        icon = self._render()
        canvas = Image.new("RGBA", (self.video_w, self.video_h), (0, 0, 0, 0))
        iw, ih = icon.size
        ix = int(self.video_w * self.pos_cx) - iw // 2
        iy = int(self.video_h * self.pos_cy) - ih // 2
        canvas.paste(icon, (ix, iy), icon)
        return ImageClip(np.array(canvas), duration=duration).with_start(start)
