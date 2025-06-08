from dataclasses import dataclass, fields

from ulauncher.config import PATHS
from ulauncher.utils.json_utils import json_load, json_save

_settings_file = f"{PATHS.CONFIG}/settings.json"


@dataclass()
class Settings:
    clear_previous_query: bool = True
    grab_mouse_pointer: bool = False
    jump_keys: str = "1234567890abcdefghijklmnopqrstuvwxyz"
    max_recent_apps: int = 0
    raise_if_started: bool = False
    render_on_screen: str = "mouse-pointer-monitor"
    terminal_command: str = ""
    theme_name: str = "light"
    arrow_key_aliases: str = "hjkl"
    # Additional fields found in the settings file
    blacklisted_desktop_dirs: str = ""
    disable_desktop_filters: bool = False
    enable_application_mode: bool = True
    show_indicator_icon: bool = True
    show_recent_apps: str = "0"

    def get_jump_keys(self):
        # convert to list and filter out duplicates
        return list(dict.fromkeys(list(self.jump_keys)))

    def save(self):
        """Save current settings to JSON file"""
        # Convert to dict, handling dash/underscore conversion for compatibility
        data = {}
        for key, value in self.__dict__.items():
            # Convert underscores back to dashes for JSON storage
            json_key = key.replace("_", "-")
            data[json_key] = value
        json_save(data, _settings_file)

    @classmethod
    def load_from_file(cls):
        """Load settings from JSON file"""
        data = json_load(_settings_file)
        # Convert dash to underscore for attribute names
        normalized_data = {}
        # Get the field names from the dataclass
        field_names = {f.name for f in fields(cls)}

        for key, value in data.items():
            normalized_key = key.replace("-", "_")
            # Only include fields that are defined in the dataclass
            if normalized_key in field_names:
                normalized_data[normalized_key] = value

        return cls(**normalized_data)


# Singleton instance holder
_settings_instance = None


def get_settings() -> Settings:
    """Get the singleton settings instance, loading from file on first call"""
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = Settings.load_from_file()
    return _settings_instance
