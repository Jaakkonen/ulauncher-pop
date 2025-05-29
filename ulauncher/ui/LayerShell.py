"""
Allows for a window to opt in to the wayland layer shell protocol.

This disables decorations and displays the window on top of other applications (even if fullscreen).
Uses the wlr-layer-shell protocol [1]

[1]: https://gitlab.freedesktop.org/wlroots/wlr-protocols/-/blob/master/unstable/wlr-layer-shell-unstable-v1.xml
"""

# TODO: Reimplement this with GTK4-supporting library.
# from typing import Optional, TypeGuard

# import gi
# from gi.repository import Gtk

# try:
#     gi.require_version("GtkLayerShell", "0.1")
#     from gi.repository import GtkLayerShell  # type: ignore[attr-defined]
# except (ValueError, ImportError):
#     GtkLayerShell = None


# _is_supported = GtkLayerShell is not None and GtkLayerShell.is_supported()
# def is_supported(v: Optional[GtkLayerShell] = GtkLayerShell) -> TypeGuard[GtkLayerShell]:
#     """Check if running under a wayland compositor that supports the layer shell extension"""
#     return _is_supported


# def enable(window: Gtk.Window) -> bool:
#     if not is_supported(GtkLayerShell):
#         return False

#     GtkLayerShell.init_for_window(window)
#     GtkLayerShell.set_keyboard_mode(window, GtkLayerShell.KeyboardMode.EXCLUSIVE)
#     GtkLayerShell.set_layer(window, GtkLayerShell.Layer.OVERLAY)
#     # Ask to be moved when over some other shell component
#     GtkLayerShell.set_exclusive_zone(window, 0)
#     return True


# def set_vertical_position(window: Gtk.Window, pos_y: float) -> None:
#     if not is_supported(GtkLayerShell):
#         return
#     # Set vertical position and anchor to the top edge, will be centered horizontally
#     # by default
#     GtkLayerShell.set_anchor(window, GtkLayerShell.Edge.TOP, True)
#     GtkLayerShell.set_margin(window, GtkLayerShell.Edge.TOP, pos_y)
