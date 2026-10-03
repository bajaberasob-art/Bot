"""Shared defaults and safe message formatting for PRIME level controls."""
from copy import deepcopy
import re
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


DEFAULT_CONTROLS = {
    "rank": {
        "enabled": True,
        "imageOnly": True,
        "sendEmbed": False,
        "showCustomMessage": False,
        "customMessage": "",
        "showCard": True,
        "channels": [],
    },
    "levelup": {
        "sendNotification": True,
        "sendAsEmbed": True,
        "showRankCard": True,
        "mentionUser": True,
        "mentionRole": "",
        "embedTitle": "🎉 Level Up!",
        "embedColor": "#12D6FF",
        "embedFooter": "",
        "embedThumbnail": "",
        "embedImage": "",
        "timestamp": False,
    },
    "top": {
        "enabled": True,
        "defaultMode": "text",
        "count": 10,
        "showAvatar": True,
        "showProgress": True,
        "embed": True,
        "embedTitle": "🏆 PRIME TOP",
        "embedMessage": "ترتيب XP للفترة المحددة.",
        "embedColor": "#12D6FF",
    },
    "notifications": {
        "milestone": {
            "sendAsEmbed": False,
            "mentionUser": True,
            "mentionRole": "",
            "embedTitle": "إنجاز جديد",
            "embedColor": "#12D6FF",
            "embedFooter": "",
            "timestamp": False,
        },
        "overtake": {
            "sendAsEmbed": False,
            "mentionUser": True,
            "mentionRole": "",
            "embedTitle": "تجاوز في PRIME TOP",
            "embedColor": "#12D6FF",
            "embedFooter": "",
            "timestamp": False,
        },
    },
    "periodic": {
        "daily": {
            "enabled": False, "channel": "", "time": "09:00", "timezone": "UTC",
            "rewardRole": "", "winners": 1, "message": "🏆 الفائز بـ TOP اليوم: {mention} · {xp} XP",
            "embed": True, "embedTitle": "🏆 PRIME Daily TOP",
            "embedDescription": "{message}", "embedColor": "#12D6FF",
            "mentionWinners": True, "showXp": True, "showRank": True,
        },
        "weekly": {
            "enabled": False, "channel": "", "time": "18:00", "timezone": "UTC",
            "weekday": 4, "rewardRole": "", "winners": 1,
            "message": "🏆 الفائز بـ TOP الأسبوعي: {mention} · {xp} XP",
            "embed": True, "embedTitle": "🏆 PRIME Weekly TOP",
            "embedDescription": "{message}", "embedColor": "#4263EB",
            "mentionWinners": True, "showXp": True, "showRank": True,
        },
        "monthly": {
            "enabled": False, "channel": "", "time": "20:00", "timezone": "UTC",
            "dayOfMonth": 1, "rewardRole": "", "winners": 1,
            "message": "🏆 الفائز بـ TOP الشهري: {mention} · {xp} XP",
            "embed": True, "embedTitle": "🏆 PRIME Monthly TOP",
            "embedDescription": "{message}", "embedColor": "#8B5CF6",
            "mentionWinners": True, "showXp": True, "showRank": True,
        },
    },
}


def controls_with_defaults(value=None, settings=None):
    """Merge persisted controls over defaults and migrate legacy level-up values."""
    result = deepcopy(DEFAULT_CONTROLS)
    if isinstance(value, dict):
        for section, defaults in DEFAULT_CONTROLS.items():
            source = value.get(section)
            if isinstance(defaults, dict) and isinstance(source, dict):
                if section == "periodic" or section == "notifications":
                    for key, nested_defaults in defaults.items():
                        nested_source = source.get(key)
                        if isinstance(nested_source, dict):
                            result[section][key].update(nested_source)
                else:
                    result[section].update(source)
    settings = settings or {}
    if not isinstance(value, dict) or "channels" not in value.get("rank", {}):
        result["rank"]["channels"] = [
            str(item) for item in settings.get("command_rank_channels", [])
        ]
    if not isinstance(value, dict) or "embedTitle" not in value.get("levelup", {}):
        result["levelup"]["embedTitle"] = settings.get("levelup_title") or "🎉 Level Up!"
    return result


class SafeTemplateValues(dict):
    """Unknown placeholders remain visible instead of raising in event listeners."""
    def __missing__(self, key):
        return "{" + str(key) + "}"


def render_template(template, values):
    try:
        return str(template or "").format_map(SafeTemplateValues(values)).strip()
    except (ValueError, IndexError, AttributeError):
        return str(template or "").strip()


def _bool(value, name):
    if not isinstance(value, bool):
        raise ValueError(f"{name} must be boolean")
    return value


def _text(value, name, maximum):
    if not isinstance(value, str) or len(value) > maximum:
        raise ValueError(f"{name} must be text under {maximum + 1} characters")
    return value.strip()


def _color(value, name):
    if not isinstance(value, str) or not re.fullmatch(r"#[0-9a-fA-F]{6}", value):
        raise ValueError(f"invalid {name}")
    return value.lower()


def _integer(value, name, minimum, maximum):
    if isinstance(value, bool) or not isinstance(value, int) or not minimum <= value <= maximum:
        raise ValueError(f"{name} is outside the allowed range")
    return value


def validate_controls(
    value, legacy_settings, *, validate_channel, validate_role,
    validate_assignable_role,
):
    result = controls_with_defaults(value, legacy_settings)
    rank = result["rank"]
    for key in ("enabled", "imageOnly", "sendEmbed", "showCustomMessage", "showCard"):
        rank[key] = _bool(rank.get(key), f"rank.{key}")
    rank["customMessage"] = _text(rank.get("customMessage"), "rank.customMessage", 500)
    if not isinstance(rank.get("channels"), list) or len(rank["channels"]) > 200:
        raise ValueError("rank.channels must be an array with at most 200 entries")
    rank["channels"] = list(dict.fromkeys(
        str(validate_channel(item)) for item in rank["channels"] if item
    ))

    levelup = result["levelup"]
    for key in ("sendNotification", "sendAsEmbed", "showRankCard", "mentionUser", "timestamp"):
        levelup[key] = _bool(levelup.get(key), f"levelup.{key}")
    role = levelup.get("mentionRole")
    levelup["mentionRole"] = str(validate_role(role)) if role else ""
    levelup["embedTitle"] = _text(levelup.get("embedTitle"), "levelup.embedTitle", 256)
    levelup["embedFooter"] = _text(levelup.get("embedFooter"), "levelup.embedFooter", 2048)
    levelup["embedColor"] = _color(levelup.get("embedColor"), "levelup.embedColor")
    for key in ("embedThumbnail", "embedImage"):
        url = _text(levelup.get(key, ""), f"levelup.{key}", 400)
        if url and not url.startswith("https://"):
            raise ValueError(f"levelup.{key} must use HTTPS")
        levelup[key] = url

    top = result["top"]
    for key in ("enabled", "showAvatar", "showProgress", "embed"):
        top[key] = _bool(top.get(key), f"top.{key}")
    if top.get("defaultMode") not in {"text", "voice"}:
        raise ValueError("top.defaultMode must be text or voice")
    top["count"] = _integer(top.get("count"), "top.count", 1, 20)
    top["embedTitle"] = _text(top.get("embedTitle"), "top.embedTitle", 256)
    top["embedMessage"] = _text(top.get("embedMessage"), "top.embedMessage", 1000)
    top["embedColor"] = _color(top.get("embedColor"), "top.embedColor")

    for name in ("milestone", "overtake"):
        item = result["notifications"][name]
        for key in ("sendAsEmbed", "mentionUser", "timestamp"):
            item[key] = _bool(item.get(key), f"notifications.{name}.{key}")
        role = item.get("mentionRole")
        item["mentionRole"] = str(validate_role(role)) if role else ""
        item["embedTitle"] = _text(item.get("embedTitle"), f"{name}.embedTitle", 256)
        item["embedFooter"] = _text(item.get("embedFooter"), f"{name}.embedFooter", 2048)
        item["embedColor"] = _color(item.get("embedColor"), f"{name}.embedColor")

    for period in ("daily", "weekly", "monthly"):
        item = result["periodic"][period]
        item["enabled"] = _bool(item.get("enabled"), f"{period}.enabled")
        for key in ("embed", "mentionWinners", "showXp", "showRank"):
            item[key] = _bool(item.get(key), f"{period}.{key}")
        channel = item.get("channel")
        item["channel"] = str(validate_channel(channel, messageable=True)) if channel else ""
        role = item.get("rewardRole")
        item["rewardRole"] = str(validate_assignable_role(role)) if role else ""
        if not isinstance(item.get("time"), str) or not re.fullmatch(
            r"(?:[01]\d|2[0-3]):[0-5]\d", item["time"],
        ):
            raise ValueError(f"{period}.time must use HH:MM")
        zone = _text(item.get("timezone"), f"{period}.timezone", 64)
        try:
            ZoneInfo(zone)
        except (ZoneInfoNotFoundError, ValueError):
            raise ValueError(f"{period}.timezone is not supported")
        item["timezone"] = zone
        item["winners"] = _integer(item.get("winners"), f"{period}.winners", 1, 20)
        if period == "weekly":
            item["weekday"] = _integer(item.get("weekday"), "weekly.weekday", 0, 6)
        if period == "monthly":
            item["dayOfMonth"] = _integer(item.get("dayOfMonth"), "monthly.dayOfMonth", 1, 28)
        item["message"] = _text(item.get("message"), f"{period}.message", 1000)
        item["embedTitle"] = _text(item.get("embedTitle"), f"{period}.embedTitle", 256)
        item["embedDescription"] = _text(
            item.get("embedDescription"), f"{period}.embedDescription", 4000,
        )
        item["embedColor"] = _color(item.get("embedColor"), f"{period}.embedColor")
        if item["enabled"] and not item["channel"]:
            raise ValueError(f"{period} TOP requires a channel")
    return result