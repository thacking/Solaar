import json
import os

CONFIG_DIR = os.path.expanduser("~/.config/haptics")
CONFIG_FILE = os.path.join(CONFIG_DIR, "settings.json")

DEFAULT_CONFIG = {
    "notifications": {
        "enabled": True,
        "default_wave": "HAPPY ALERT",
        "custom": []
    },
    "cursor": {
        "link_wave": "DAMP STATE CHANGE"
    }
}


def load_config():
    if not os.path.exists(CONFIG_FILE):
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG

    with open(CONFIG_FILE, "r") as f:
        return json.load(f)


def save_config(config):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, sort_keys=False)
