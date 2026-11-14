"""Scoreboard and flip-counter overlay matching the 'YEARS AT WAR' board in reference video."""

from __future__ import annotations
from typing import Optional, Tuple
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy import ImageClip, VideoClip


# Color palette from reference video
BOARD_BG = (101, 67, 33)         # dark wood brown
BOARD_BORDER = (139, 90, 43)     # lighter wood
LABEL_RED = (192, 30, 45)        # team red
LABEL_TEAL = (0, 150, 136)       # team teal
DIGIT_BG = (245, 240, 220)       # cream/ivory
DIGIT_FG = (20, 20, 20)          # near-black
DIGIT_SHADOW = (180, 170, 140)   # digit card shadow
DIGIT_DIVIDER = (80, 60, 30)     # dark brown divider line


def _load_font(size: int, bold: bool = True) -> ImageFont.FreeTypeFont:
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/ubuntu/Ubuntu-B.ttf",
    ]
    for c in candidates:
        try:
            return ImageFont.truetype(c, size)
        except OSError:
            continue
    return ImageFont.load_default()


class FlipCounter:
    """
    Animated 3-digit flip counter (like the '099' in reference video).
    Renders a single frame given a numeric value 0–999.
    """

    def __init__(self, digit_w: int = 60, digit_h: int = 80):
        self.digit_w = digit_w
        self.digit_h = digit_h
        self.font = _load_font(int(digit_h * 0.7))

    def render_digit(self, ch: str) -> Image.Image:
        """Render one digit tile."""
        w, h = self.digit_w, self.digit_h
        img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        # Card background with rounded shadow
        margin = 4
        draw.rectangle([margin, margin, w - margin, h - margin],
                       fill=DIGIT_SHADOW, outline=DIGIT_DIVIDER, width=2)
        draw.rectangle([margin, margin, w - margin - 2, h - margin - 2],
                       fill=DIGIT_BG, outline=DIGIT_DIVIDER, width=2)
        # Divider line across middle
        mid = h // 2
        draw.line([(margin, mid), (w - margin, mid)], fill=DIGIT_DIVIDER, width=2)
        # Digit text centered
        bbox = draw.textbbox((0, 0), ch, font=self.font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        tx = (w - tw) // 2 - bbox[0]
        ty = (h - th) // 2 - bbox[1]
        draw.text((tx, ty), ch, font=self.font, fill=DIGIT_FG)
        return img

    def render(self, value: int) -> Image.Image:
        """Render all 3 digit tiles side by side."""
        s = f"{max(0, min(999, value)):03d}"
        gap = 6
        total_w = self.digit_w * 3 + gap * 2
        img = Image.new("RGBA", (total_w, self.digit_h), (0, 0, 0, 0))
        for i, ch in enumerate(s):
            tile = self.render_digit(ch)
            img.paste(tile, (i * (self.digit_w + gap), 0), tile)
        return img


class ScoreboardOverlay:
    """
    Full 'YEARS AT WAR' style scoreboard board.
    Renders as a wooden-plank sign with:
      - Two-color split label (red | teal)
      - Flip counter showing a number
      - Optional tally marks
    """

    def __init__(
        self,
        label_left: str = "YEARS",
        label_right: str = "AT WAR",
        board_w: int = 380,
        board_h: int = 220,
        video_size: Tuple[int, int] = (576, 1024),
        position: Tuple[float, float] = (0.5, 0.35),  # center-x, 35% from top
    ):
        self.label_left = label_left
        self.label_right = label_right
        self.board_w = board_w
        self.board_h = board_h
        self.video_w, self.video_h = video_size
        self.pos_cx, self.pos_cy = position
        self.counter = FlipCounter(digit_w=70, digit_h=90)
        self._label_font = _load_font(32)
        self._tally_font = _load_font(14, bold=False)

    def _render_board(self, value: int, tally_count: int = 0) -> Image.Image:
        bw, bh = self.board_w, self.board_h
        img = Image.new("RGBA", (bw, bh), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Board body
        border = 8
        draw.rectangle([0, 0, bw - 1, bh - 1], fill=BOARD_BORDER)
        draw.rectangle([border, border, bw - border - 1, bh - border - 1],
                       fill=BOARD_BG)

        # Split label row at top
        label_h = 48
        half = bw // 2
        draw.rectangle([border, border, half, border + label_h],
                       fill=LABEL_RED)
        draw.rectangle([half, border, bw - border, border + label_h],
                       fill=LABEL_TEAL)

        # Label texts
        def draw_label(text, x, font_color=(255, 255, 255)):
            bb = draw.textbbox((0, 0), text, font=self._label_font)
            tw = bb[2] - bb[0]
            th = bb[3] - bb[1]
            cx = x - bb[0]
            cy = border + (label_h - th) // 2 - bb[1]
            draw.text((cx, cy), text, font=self._label_font, fill=font_color)

        draw_label(self.label_left, bw // 4)
        draw_label(self.label_right, bw * 3 // 4)

        # Counter
        counter_img = self.counter.render(value)
        cw, ch = counter_img.size
        cx = (bw - cw) // 2
        cy = border + label_h + (bh - border - label_h - ch) // 2
        img.paste(counter_img, (cx, cy), counter_img)

        # Tally marks (optional)
        if tally_count > 0:
            ty = bh - border - 20
            tx = border + 10
            draw.text((tx, ty), "│" * tally_count, font=self._tally_font,
                      fill=(180, 160, 120))

        return img

    def make_clip(self, value: int, duration: float, start: float = 0.0,
                  tally_count: int = 0) -> ImageClip:
        """Static scoreboard clip."""
        board = self._render_board(value, tally_count)
        canvas = Image.new("RGBA", (self.video_w, self.video_h), (0, 0, 0, 0))
        bx = int(self.video_w * self.pos_cx) - self.board_w // 2
        by = int(self.video_h * self.pos_cy) - self.board_h // 2
        canvas.paste(board, (bx, by), board)
        arr = np.array(canvas)
        return ImageClip(arr, duration=duration).with_start(start)

    def make_animated_clip(
        self,
        start_value: int,
        end_value: int,
        duration: float,
        start: float = 0.0,
    ) -> VideoClip:
        """
        Animated clip that counts from start_value to end_value over duration.
        Uses a smooth easing curve.
        """
        video_w, video_h = self.video_w, self.video_h
        board_w, board_h = self.board_w, self.board_h
        pos_cx, pos_cy = self.pos_cx, self.pos_cy
        counter = self.counter
        label_left = self.label_left
        label_right = self.label_right
        label_font = self._label_font
        sb = self  # keep ref for _render_board

        def make_frame(t: float) -> np.ndarray:
            # Ease-out cubic
            p = t / duration
            p_eased = 1 - (1 - p) ** 3
            value = int(start_value + (end_value - start_value) * p_eased)
            board = sb._render_board(value)
            canvas = Image.new("RGBA", (video_w, video_h), (0, 0, 0, 0))
            bx = int(video_w * pos_cx) - board_w // 2
            by = int(video_h * pos_cy) - board_h // 2
            canvas.paste(board, (bx, by), board)
            return np.array(canvas)

        return VideoClip(make_frame, duration=duration).with_start(start)
