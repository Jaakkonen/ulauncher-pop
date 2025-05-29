from __future__ import annotations

import logging
from os.path import expanduser, isfile, join

from gi.repository import Gdk, Gtk

icon_theme = Gtk.IconTheme.get_for_display(Gdk.Display.get_default())
logger = logging.getLogger()


def get_icon_path(icon: str, size: int = 32, base_path: str = "") -> str | None:
    """
    :param str icon:
    :rtype: str
    """
    try:
        if icon and isinstance(icon, str):
            icon = expanduser(icon)
            if icon.startswith("/"):
                return icon

            expanded_path = join(base_path, icon)
            if isfile(expanded_path):
                return expanded_path

            themed_icon = icon_theme.lookup_icon(
                icon,          # icon_name
                None,          # fallbacks
                size,          # size
                1,             # scale
                Gtk.TextDirection.NONE,  # direction
                Gtk.IconLookupFlags(0)   # flags
            )
            if themed_icon:
                icon_file = themed_icon.get_file()
                if icon_file:
                    return icon_file.get_path()

    except Exception as err:
        logger.warning("Error '%s' occurred when trying to load icon path '%s'.", err, icon)
        logger.info("If this happens often, please see https://github.com/Ulauncher/Ulauncher/discussions/1346")

    return None
