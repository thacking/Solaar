import json
import logging
import os
from dataclasses import dataclass
from fnmatch import fnmatch

logger = logging.getLogger(__name__)

DEFAULT_RULES_PATH = os.path.expanduser("~/.config/haptics/settings.json")


@dataclass
class CustomRule:
    name: str               # rule name
    pattern_app: str        # app name filter
    pattern_summary: str    # summary/title filter
    pattern_body: str       # content/body filter
    wave: str               # wave name


@dataclass
class NotificationSettings:
    enabled: bool
    default_wave: str
    rules: list[CustomRule]


def _match_field(pattern: str, value: str) -> bool:
    if pattern is None or pattern == "" or pattern == "*":
        return True
    if value is None:
        value = ""
    pattern = pattern.lower()
    value = value.lower()
    return fnmatch(value, pattern)


def load_rules(path: str = DEFAULT_RULES_PATH) -> NotificationSettings:
    if not os.path.exists(path):
        logger.info("No settings file found (%s), notifications disabled.", path)
        return NotificationSettings(enabled=False, default_wave="HAPPY ALERT", rules=[])

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f) or {}
    except Exception as exc:
        logger.error("Error while loading settings from %s: %s", path, exc)
        return NotificationSettings(enabled=False, default_wave="HAPPY ALERT", rules=[])

    if not isinstance(data, dict):
        logger.error("settings.json has unexpected format (not a dict): %r", data)
        return NotificationSettings(enabled=False, default_wave="HAPPY ALERT", rules=[])

    notifications = data.get("notifications", {}) or {}

    enabled = bool(notifications.get("enabled", True))
    default_wave = notifications.get("default_wave", "HAPPY ALERT")

    custom_list = notifications.get("custom", []) or []
    if not isinstance(custom_list, list):
        logger.error("notifications.custom is not a list: %r", custom_list)
        custom_list = []

    rules: list[CustomRule] = []
    for idx, item in enumerate(custom_list):
        try:
            rules.append(
                CustomRule(
                    name=item.get("name", f"rule_{idx}"),
                    pattern_app=item.get("pattern_app", "*"),
                    pattern_summary=item.get("pattern_summary", "*"),
                    pattern_body=item.get("pattern_body", "*"),
                    wave=item.get("wave", default_wave),
                )
            )
        except Exception as exc:
            logger.error("Error in custom rule %d (%r): %s", idx, item, exc)

    logger.info(
        "Loaded settings from %s: enabled=%s, default_wave=%r, %d custom rules.",
        path,
        enabled,
        default_wave,
        len(rules),
    )

    return NotificationSettings(
        enabled=enabled,
        default_wave=default_wave,
        rules=rules,
    )


def select_wave_for_notification(
    app_name: str | None,
    summary: str | None,
    body: str | None,
    settings: NotificationSettings,
) -> str | None:
    if not settings.enabled:
        logger.debug("Notifications disabled in settings → no wave.")
        logger.debug("Loaded settings: %r", settings)

        return None

    app_name = app_name or ""
    summary = summary or ""
    body = body or ""

    for idx, rule in enumerate(settings.rules):
        if not _match_field(rule.pattern_app, app_name):
            continue
        if not _match_field(rule.pattern_summary, summary):
            continue
        if not _match_field(rule.pattern_body, body):
            continue

        logger.debug(
            "Rule #%d (%s) matched: app=%r summary=%r body=%r -> wave=%r",
            idx,
            rule.name,
            app_name,
            summary,
            body,
            rule.wave,
        )
        return rule.wave

    logger.debug(
        "No rule matched for: app=%r summary=%r body=%r -> default_wave=%r",
        app_name,
        summary,
        body,
        settings.default_wave,
    )
    return settings.default_wave