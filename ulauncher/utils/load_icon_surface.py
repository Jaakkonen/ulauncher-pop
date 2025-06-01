from __future__ import annotations

import logging
from functools import lru_cache
from os.path import expanduser, isfile

from gi.repository import Gdk, Gio, Gtk

from ulauncher.config import PATHS

logger = logging.getLogger()

DEFAULT_EXE_ICON = "application-x-executable"


@lru_cache(maxsize=50)
def load_icon_paintable(icon: str, scale_factor: int = 1) -> Gtk.IconPaintable:
    """
    Load an icon as a Gtk.IconPaintable for GTK4.
    Finds the best quality icon available and lets CSS handle sizing.
    """
    if not icon:
        icon = DEFAULT_EXE_ICON

    display = Gdk.Display.get_default()
    icon_theme = Gtk.IconTheme.get_for_display(display)

    # Handle absolute paths for custom icons
    if icon.startswith("/"):
        icon = expanduser(icon)
        if isfile(icon):
            try:
                # For custom icon files, load at high resolution for best quality
                gfile = Gio.File.new_for_path(icon)
                return Gtk.IconPaintable.new_for_file(gfile, 128, scale_factor)
            except Exception as e:
                logger.warning("Could not load custom icon %s (%s). Using fallback.", icon, e)
                icon = DEFAULT_EXE_ICON

    # For themed icons - look for best quality available
    # Try different sizes to find the best quality icon, starting with higher resolutions
    for size in [128, 96, 64, 48, 32, 24, 16]:
        try:
            paintable = icon_theme.lookup_icon(
                icon,
                None,  # fallbacks
                size,
                scale_factor,
                Gtk.TextDirection.NONE,
                0  # No flags - let GTK choose the best approach
            )
            if paintable:
                return paintable
        except Exception:
            continue

    logger.warning("Could not find themed icon %s. Using fallback.", icon)

    # Final fallback to default executable icon
    for size in [128, 96, 64, 48, 32, 24, 16]:
        try:
            paintable = icon_theme.lookup_icon(
                DEFAULT_EXE_ICON,
                None,
                size,
                scale_factor,
                Gtk.TextDirection.NONE,
                0
            )
            if paintable:
                return paintable
        except Exception:
            continue

    logger.error("Could not load fallback icon %s", DEFAULT_EXE_ICON)

    # Ultimate fallback - use missing image icon
    return icon_theme.lookup_icon(
        "image-missing",
        None,
        32,
        scale_factor,
        Gtk.TextDirection.NONE,
        0
    )

