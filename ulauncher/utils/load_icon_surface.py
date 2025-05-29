from __future__ import annotations

import logging
from functools import lru_cache

from gi.repository import Gdk, GdkPixbuf

from ulauncher.config import PATHS
from ulauncher.utils.get_icon_path import get_icon_path

logger = logging.getLogger()

DEFAULT_EXE_ICON = f"{PATHS.ASSETS}/icons/executable.png"


@lru_cache(maxsize=50)
def load_icon_texture(icon: str, size: int, scaling_factor: int = 1) -> Gdk.Texture:
    """
    Load an icon as a GdkTexture for GTK4.
    This is the GTK4 replacement for load_icon_surface.
    """
    real_size = size * scaling_factor
    icon_path = None
    try:
        icon_path = get_icon_path(icon, real_size) or DEFAULT_EXE_ICON

        # GTK4: Use texture creation directly from file when possible
        # This avoids deprecated pixbuf APIs
        try:
            return Gdk.Texture.new_from_file(Gdk.File.new_for_path(icon_path))
        except Exception:
            # Fallback to pixbuf approach for scaling if direct loading fails
            pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(icon_path, real_size, real_size)
            assert pixbuf
            # Use the deprecated API for now, but it still works in GTK4
            # TODO: Replace with a better approach when available
            return Gdk.Texture.new_for_pixbuf(pixbuf)
    except Exception as e:
        if icon_path == DEFAULT_EXE_ICON:
            msg = f"Could not load fallback icon: {icon_path}"
            raise RuntimeError(msg) from e

        logger.warning("Could not load specified icon %s (%s). Will use fallback icon", icon, e)
        return load_icon_texture(DEFAULT_EXE_ICON, size, scaling_factor)


# Keep backward compatibility
@lru_cache(maxsize=50)
def load_icon_surface(icon: str, size: int, scaling_factor: int = 1):
    """
    Deprecated: Use load_icon_texture instead.
    This function is kept for backward compatibility but should be updated.
    """
    logger.warning("load_icon_surface is deprecated, use load_icon_texture instead")
    return load_icon_texture(icon, size, scaling_factor)
