"""Phase 5 memory-only rank cards. Import and await; this is not a Discord cog.

text_xp is cumulative database XP. next_level_xp is the XP cost of advancing
from text_level, not a cumulative threshold. Optional statistics are supplied
in settings: total_messages, total_voice_seconds, current_streak.
"""
import asyncio
import io
import random
import unicodedata
import weakref
from pathlib import Path

import arabic_reshaper
import discord
from bidi.algorithm import get_display
from PIL import Image, ImageColor, ImageDraw, ImageFilter, ImageFont, ImageOps

from cogs.card_images import fetch_image
from level_progression import total_xp_for_level, xp_required

LAYOUTS = {"vertical": (560, 900), "stats": (1000, 420), "minimal": (900, 230),
           "ring": (620, 680), "classic": (1000, 340)}
PARTICLES = {"none", "sparks", "shine", "embers", "snow", "petals", "neon"}
FONT_DIR = Path(__file__).resolve().parents[1] / "assets" / "fonts"
_gates = weakref.WeakKeyDictionary()
SCALE = 2
WHITE = "#f8f5fc"
MUTED = "#aaa5ba"


def number(value, default=0):
    try:
        value = int(value)
        return max(0, min(value, 10**18))
    except (ValueError, TypeError, OverflowError):
        return default


def calculate_progress(text_level, text_xp, next_level_xp):
    """Return (XP within level, cost to next level, clamped fraction)."""
    level = number(text_level)
    required = number(next_level_xp)
    earned = max(0, number(text_xp) - total_xp_for_level(level))
    return earned, required, min(1.0, max(0.0, earned / required)) if required else 0.0


def display_text(value):
    text = "".join(c for c in str(value)[:160]
                   if unicodedata.category(c) not in {"Cc", "Cf", "Cs"})
    # BASIC font layout + explicit shaping is portable to Pillow builds without RAQM.
    return get_display(arabic_reshaper.reshape(text))


def compact(value):
    value = number(value)
    for limit, suffix in ((10**12, "T"), (10**9, "B"), (10**6, "M")):
        if value >= limit:
            return f"{value / limit:.1f}{suffix}"
    return f"{value:,}"


class Card:
    def __init__(self, size, color, background, mode):
        self.w, self.h = size
        self.accent = color
        self.image = Image.new("RGB", (self.w * SCALE, self.h * SCALE), "#07070b")
        if background:
            with Image.open(io.BytesIO(background)) as source:
                fitted = ImageOps.fit(source.convert("RGB"), self.image.size, method=Image.Resampling.LANCZOS)
                self.image = Image.blend(self.image, fitted, 0.33)
        glow = Image.new("RGB", (self.w // 4, self.h // 4), "#000000")
        gd = ImageDraw.Draw(glow)
        gd.ellipse((-40, -50, self.w // 4, self.h // 6), fill=color)
        gd.ellipse((self.w // 8, self.h // 7, self.w // 3, self.h // 3), fill="#554bcd")
        glow = glow.filter(ImageFilter.GaussianBlur(35)).resize(self.image.size, Image.Resampling.BILINEAR)
        self.image = Image.blend(self.image, glow, 0.10)
        self.draw = ImageDraw.Draw(self.image)
        self.fonts = {}
        self.panel((12, 12, self.w - 12, self.h - 12), radius=28, fill=None)
        self.particles(mode)

    def font(self, size, bold=False, emoji=False):
        key = (size, bold, emoji)
        if key not in self.fonts:
            path = FONT_DIR / ("NotoEmoji.ttf" if emoji else
                               ("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"))
            try:
                self.fonts[key] = ImageFont.truetype(
                    str(path), size * SCALE, layout_engine=ImageFont.Layout.BASIC)
            except OSError:
                self.fonts[key] = ImageFont.load_default(size=size * SCALE)
        return self.fonts[key]

    def text_runs(self, text, size, bold):
        runs = []
        for char in text:
            emoji = ord(char) >= 0x1F000 or 0x2600 <= ord(char) <= 0x27BF
            if runs and runs[-1][0] == emoji:
                runs[-1][1] += char
            else:
                runs.append([emoji, char])
        return [(part, self.font(size, bold, emoji)) for emoji, part in runs]

    def text(self, xy, value, size=18, color=WHITE, bold=False, width=None, center=False):
        text = display_text(value)
        def measure(content):
            return sum(self.draw.textlength(part, font=font)
                       for part, font in self.text_runs(content, size, bold))
        if width:
            while text and measure(text) > width * SCALE:
                text = text[:-2] + "…" if len(text) > 2 else ""
        x, y = xy
        if center:
            x -= measure(text) / (2 * SCALE)
        for part, font in self.text_runs(text, size, bold):
            self.draw.text((x * SCALE, y * SCALE), part, font=font, fill=color, stroke_width=0)
            x += self.draw.textlength(part, font=font) / SCALE

    def panel(self, box, radius=18, fill="#12121c", outline="#35323f"):
        self.draw.rounded_rectangle(tuple(int(v * SCALE) for v in box), radius=radius * SCALE,
                                    fill=fill, outline=outline, width=SCALE)

    def line(self, box, color="#302d3c", width=1):
        self.draw.line(tuple(v * SCALE for v in box), fill=color, width=width * SCALE)

    def particles(self, mode):
        if not isinstance(mode, str) or mode not in PARTICLES or mode == "none":
            return
        rng = random.Random(715)
        # Sparse backdrop effects stay behind the avatar and readable panels.
        for _ in range(max(8, min(32, self.w*self.h//20000))):
            x = rng.choice([rng.randint(20, 28), rng.randint(self.w-28, self.w-20)])
            y = rng.randint(22, self.h - 22)
            r = rng.choice([1, 2, 3])
            color = {"sparks": "#e6b6d2", "shine": "#cbc4f7", "embers": "#ba695d",
                     "snow": "#ccd6e9", "petals": "#ac7790", "neon": self.accent}[mode]
            if mode in {"shine", "neon"}:
                self.line((x - r * 2, y, x + r * 2, y), color)
                self.line((x, y - r * 2, x, y + r * 2), color)
            elif mode == "sparks":
                self.line((x, y, x + 3, y - 6), color)
            else:
                self.draw.ellipse(((x-r)*SCALE, (y-r)*SCALE, (x+r)*SCALE,
                                   (y+r*(2 if mode == "petals" else 1))*SCALE), fill=color)

    def avatar(self, xy, diameter, data, progress=None):
        x, y = xy
        ring = Image.new("RGBA", self.image.size)
        rd = ImageDraw.Draw(ring)
        bounds = tuple(int(v * SCALE) for v in (x-6, y-6, x+diameter+6, y+diameter+6))
        rd.ellipse(bounds, outline=self.accent, width=5*SCALE)
        self.image.paste(ring.filter(ImageFilter.GaussianBlur(9*SCALE)), (0, 0),
                         ring.filter(ImageFilter.GaussianBlur(9*SCALE)))
        self.draw = ImageDraw.Draw(self.image)
        self.draw.ellipse(bounds, outline="#484153", width=2*SCALE)
        if progress is not None and progress > 0:
            self.draw.arc(bounds, -90, -90 + progress * 360, fill=self.accent, width=5*SCALE)
        elif progress is None:
            self.draw.ellipse(bounds, outline=self.accent, width=2*SCALE)
        size = (diameter*SCALE, diameter*SCALE)
        if data:
            with Image.open(io.BytesIO(data)) as source:
                avatar = ImageOps.fit(source.convert("RGB"), size, method=Image.Resampling.LANCZOS)
        else:
            avatar = Image.new("RGB", size, "#292137")
            ad = ImageDraw.Draw(avatar)
            d = diameter*SCALE
            ad.ellipse((d*.35, d*.2, d*.65, d*.5), fill="#b8a4cc")
            ad.ellipse((d*.2, d*.55, d*.8, d*1.13), fill="#b8a4cc")
        mask = Image.new("L", size)
        ImageDraw.Draw(mask).ellipse((0, 0, size[0]-1, size[1]-1), fill=255)
        self.image.paste(avatar, (x*SCALE, y*SCALE), mask)

    def bar(self, box, progress, animated=False):
        x, y, w, h = box
        self.panel((x, y, x+w, y+h), radius=h//2, fill="#23212e")
        fill_width = max(0, int(w*progress))
        if fill_width:
            # Clip the fill to a rounded mask; never draw a false minimum progress.
            mask = Image.new("L", (w*SCALE, h*SCALE))
            md = ImageDraw.Draw(mask)
            md.rounded_rectangle((0, 0, fill_width*SCALE-1, h*SCALE-1),
                                 radius=min(h, fill_width)*SCALE//2, fill=255)
            gradient = Image.new("RGB", (w*SCALE, h*SCALE))
            gd = ImageDraw.Draw(gradient)
            start = ImageColor.getrgb(self.accent)
            for column in range(w*SCALE):
                t = column / max(1, w*SCALE-1)
                color = tuple(int(c*(1-t*.35)+245*t*.35) for c in start)
                gd.line((column, 0, column, h*SCALE), fill=color)
            if animated:
                # Static PNG equivalent: narrow specular sheen, never GIF/APNG.
                gd.polygon([(fill_width*SCALE*.6, 0), (fill_width*SCALE*.67, 0),
                            (fill_width*SCALE*.54, h*SCALE), (fill_width*SCALE*.47, h*SCALE)],
                           fill="#fff0fb")
            self.image.paste(gradient, (x*SCALE, y*SCALE), mask)

    def stat(self, box, label, value):
        self.panel(box)
        x, y, right, _ = box
        self.text((x+18, y+13), label.upper(), 11, MUTED, width=right-x-30)
        self.text((x+18, y+35), value, 22, bold=True, width=right-x-30)


def _render(name, handle, level, xp, required, rank, total, settings, avatar, background):
    layout = settings.get("card_layout", "vertical")
    if not isinstance(layout, str) or layout not in LAYOUTS:
        layout = "vertical"
    try:
        rgb = ImageColor.getrgb(str(settings.get("card_color", "#f2aacb")))
        color = "#%02x%02x%02x" % rgb[:3]
    except (ValueError, TypeError):
        color = "#f2aacb"
    mode = settings.get("card_particles", "none")
    card = Card(LAYOUTS[layout], color, background, mode)
    earned, cost, progress = calculate_progress(level, xp, required)
    rank_text = f"#{compact(rank)}" if rank else "—"
    xp_text = f"{compact(earned)} / {compact(cost)} XP"
    animated = settings.get("card_animated_bar") in (True, 1, "1", "true")
    show_stats = settings.get("card_show_stats", True) not in (False, 0, "0", "false")
    voice = settings.get("total_voice_seconds")
    stats = [
        ("Messages", compact(settings["total_messages"]) if settings.get("total_messages") is not None else "—"),
        ("Voice time", f"{number(voice)//3600}h {(number(voice)%3600)//60}m" if voice is not None else "—"),
        ("Streak", f"{compact(settings['current_streak'])} days" if settings.get("current_streak") is not None else "—"),
    ]
    if layout == "vertical":
        card.text((36, 33), "PRIME / LEVELS", 13, color, True)
        card.text((524, 34), "", 12)
        card.panel((424, 27, 524, 69), radius=15)
        card.text((474, 35), rank_text, 20, bold=True, center=True, width=85)
        card.avatar((164, 110), 232, avatar, progress)
        card.text((280, 372), name, 30, bold=True, width=475, center=True)
        card.text((280, 417), handle, 15, MUTED, width=465, center=True)
        card.panel((32, 467, 528, 635), radius=24)
        card.text((56, 488), "TEXT LEVEL", 12, MUTED)
        card.text((55, 510), compact(level), 48, bold=True)
        card.text((468, 531), f"{progress:.0%}", 22, color, True, center=True)
        card.bar((56, 579, 448, 12), progress, animated)
        card.text((56, 603), xp_text, 14, MUTED, width=445)
        if show_stats:
            card.stat((32, 659, 270, 749), *stats[0])
            card.stat((290, 659, 528, 749), *stats[1])
            card.stat((32, 765, 270, 855), *stats[2])
            card.stat((290, 765, 528, 855), "Server rank", f"{rank_text} / {compact(total)}")
        card.text((280, 873), "GROW AT YOUR OWN PACE", 9, MUTED, center=True)
    elif layout == "stats":
        card.text((34, 30), "PRIME / MEMBER STATISTICS", 12, color, True)
        card.avatar((45, 85), 190, avatar)
        card.text((276, 75), name, 32, bold=True, width=470)
        card.text((278, 122), handle, 15, MUTED, width=430)
        card.stat((782, 55, 963, 147), "Server rank", f"{rank_text} / {compact(total)}")
        card.text((277, 176), f"Level {compact(level)}", 27, bold=True)
        card.text((277, 219), xp_text, 17, MUTED)
        card.text((944, 219), f"{progress:.0%}", 17, color, center=True)
        card.bar((278, 252, 685, 14), progress, animated)
        if show_stats:
            for index, pair in enumerate(stats):
                x = 34 + index*317
                card.stat((x, 304, x+298, 394), *pair)
    elif layout == "minimal":
        card.avatar((36, 48), 128, avatar)
        card.text((195, 33), name, 26, bold=True, width=445)
        card.text((195, 75), f"LEVEL {compact(level)}  ·  {rank_text} OF {compact(total)}", 14, color, width=650)
        card.text((195, 118), xp_text, 17, MUTED, width=530)
        card.text((830, 116), f"{progress:.0%}", 17, color, center=True)
        card.bar((196, 164, 655, 10), progress, animated)
        card.text((196, 191), "PRIME / LEVELS", 9, MUTED)
    elif layout == "ring":
        card.text((310, 31), "PRIME / PROGRESSION", 12, color, True, center=True)
        card.avatar((185, 94), 250, avatar, progress)
        card.panel((246, 320, 374, 369), radius=20, outline=color)
        card.text((310, 330), f"LVL {compact(level)}", 22, bold=True, center=True, width=115)
        card.text((310, 401), name, 30, bold=True, width=530, center=True)
        card.text((310, 447), handle, 15, MUTED, center=True, width=530)
        card.text((310, 486), f"{progress:.0%}", 35, color, True, center=True)
        card.text((310, 539), xp_text, 17, MUTED, center=True, width=510)
        card.panel((106, 591, 514, 648), radius=18)
        card.text((310, 608), f"RANK {rank_text}  /  {compact(total)} MEMBERS", 16, center=True, width=380)
    else:
        card.panel((30, 30, 970, 310), radius=25, fill="#101019")
        card.text((260, 53), "PRIME / RANK CARD", 11, color, True)
        card.avatar((58, 85), 165, avatar)
        card.text((260, 89), name, 31, bold=True, width=490)
        card.text((261, 135), handle, 15, MUTED, width=455)
        card.text((934, 70), rank_text, 27, color, True, center=True, width=85)
        card.text((900, 112), f"of {compact(total)}", 12, MUTED, center=True, width=120)
        card.line((261, 174, 938, 174))
        card.text((261, 194), f"Level {compact(level)}", 23, bold=True)
        card.text((670, 199), xp_text, 16, MUTED, width=265)
        card.bar((262, 251, 675, 17), progress, animated)
        card.text((261, 282), f"{progress:.0%} TO NEXT LEVEL", 10, MUTED)
    result = io.BytesIO()
    card.image.resize(LAYOUTS[layout], Image.Resampling.LANCZOS).save(result, format="PNG")
    result.seek(0)
    return result


async def generate_rank_card(
    user: discord.Member, text_level, text_xp, next_level_xp,
    rank_pos, total_members, settings,
) -> io.BytesIO:
    """Generate a static PNG without touching disk or querying the database.

    Await from Phase 6. CPU rendering runs in a thread with bounded concurrency.
    Missing optional statistics display an em dash, never invented values.
    """
    settings = dict(settings or {})
    name = str(getattr(user, "display_name", None) or getattr(user, "name", "Member"))
    handle = "@" + str(getattr(user, "name", "member"))
    try:
        asset = getattr(user, "display_avatar", None)
        if hasattr(asset, "with_size"):
            asset = asset.with_size(512).with_static_format("png")
        avatar_url = str(asset.url) if asset else None
    except (AttributeError, ValueError):
        avatar_url = None
    loop = asyncio.get_running_loop()
    gate = _gates.setdefault(loop, asyncio.Semaphore(3))
    async with gate:
        avatar, background = await asyncio.gather(
            fetch_image(avatar_url), fetch_image(settings.get("card_bg_url")))
        return await asyncio.to_thread(
            _render, name, handle, number(text_level), number(text_xp),
            number(next_level_xp, xp_required(number(text_level))),
            number(rank_pos), number(total_members), settings, avatar, background)