from __future__ import annotations

import logging

from gi.repository import Gdk, Gio  # type: ignore[attr-defined]

logger = logging.getLogger()


def get_monitor(use_mouse_position: bool = False) -> Gdk.Monitor | None:
    """
    :rtype: class:Gdk.Monitor
    """
    display = Gdk.Display.get_default()
    assert display

    if use_mouse_position:
        try:
            # GTK4: get_pointer() was removed, use seat API instead
            seat = display.get_default_seat()
            if seat is None:
                return None
            device = seat.get_pointer()
            if device is None:
                return None
            # GTK4: get_position() method signature changed
            surface, x, y = device.get_surface_at_position()
            if surface and hasattr(surface, "get_position"):
                x, y = surface.get_position()
                return display.get_monitor_at_point(x, y)
        except Exception:
            logger.exception("Could not get monitor with pointer position. Defaulting to first monitor")

    # GTK4: get_primary_monitor() was removed, use monitors list instead
    try:
        # Try to get the first monitor from the list
        monitors = display.get_monitors()
        if monitors and monitors.get_n_items() > 0:
            return monitors.get_item(0)
    except Exception:
        logger.exception("Could not get monitor from display. Fallback failed")

    return None


def get_text_scaling_factor() -> float:
    # GTK seems to already compensate for monitor scaling, so this just returns font scaling
    # GTK doesn't seem to allow different scaling factors on different displays
    # Text_scaling allow fractional scaling
    return Gio.Settings.new("org.gnome.desktop.interface").get_double("text-scaling-factor")

