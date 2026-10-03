"""Shared defaults and safe message formatting for PRIME level controls."""
from copy import deepcopy


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
    result["levelup"]["embedTitle"] = (
        result["levelup"].get("embedTitle")
        or settings.get("levelup_title")
        or "🎉 Level Up!"
    )
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