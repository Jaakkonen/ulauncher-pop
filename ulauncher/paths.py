import os
import sys

# spec: https://specifications.freedesktop.org/menu-spec/latest/ar01s02.html
# ULAUNCHER_SYSTEM_PREFIX is used by a third party packagers like Nix
SYSTEM_PREFIX = os.environ.get("ULAUNCHER_SYSTEM_PREFIX", sys.prefix)
# ULAUNCHER_SYSTEM_DATA_DIR is used when running in dev mode from source and during tests
ASSETS = os.path.abspath(os.environ.get("ULAUNCHER_SYSTEM_DATA_DIR", f"{SYSTEM_PREFIX}/share/ulauncher"))
HOME = os.path.expanduser("~")
CONFIG = os.path.join(os.environ.get("XDG_CONFIG_HOME", f"{HOME}/.config"), "ulauncher")
DATA = os.path.join(os.environ.get("XDG_DATA_HOME", f"{HOME}/.local/share"), "ulauncher")
STATE = os.path.join(os.environ.get("XDG_STATE_HOME", f"{HOME}/.local/state"), "ulauncher")
USER_EXTENSIONS = os.path.join(DATA, "extensions")
EXTENSIONS_CONFIG = os.path.join(CONFIG, "ext_preferences")
USER_THEMES = os.path.join(CONFIG, "user-themes")
SYSTEM_THEMES = os.path.join(ASSETS, "themes")
