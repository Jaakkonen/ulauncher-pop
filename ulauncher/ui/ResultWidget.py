from __future__ import annotations

import logging
from html import unescape

from gi.repository import Gdk, Gtk, Pango

from ulauncher.modes.poplauncher.result import Result
from ulauncher.utils.load_icon_surface import load_icon_texture
from ulauncher.utils.Settings import get_settings
from ulauncher.utils.text_highlighter import highlight_text
from ulauncher.utils.wm import get_text_scaling_factor

ELLIPSIZE_MIN_LENGTH = 6
ELLIPSIZE_FORCE_AT_LENGTH = 20
logger = logging.getLogger()


class ResultWidget(Gtk.Box):
    index: int = 0
    name: str
    query: str
    result: Result
    item_box: Gtk.Box
    shortcut_label: Gtk.Label
    title_box: Gtk.Box
    text_container: Gtk.Box

    def __init__(self, result: Result, index: int, query: str):
        super().__init__()
        self.result = result
        self.query = query
        text_scaling_factor = get_text_scaling_factor()
        icon_size = 25 if result.compact else 40
        inner_margin_x = int(12.0 * text_scaling_factor)
        outer_margin_x = int(18.0 * text_scaling_factor)
        margin_y = (3 if result.compact else 5) * text_scaling_factor

        self.add_css_class("item-frame")

        # Create click gesture for mouse clicks
        click_gesture = Gtk.GestureClick()
        click_gesture.connect("released", self.on_click)
        self.add_controller(click_gesture)

        # Create motion controller for mouse hover
        motion_controller = Gtk.EventControllerMotion()
        motion_controller.connect("enter", self.on_mouse_hover)
        self.add_controller(motion_controller)

        self.item_box = Gtk.Box()
        self.item_box.add_css_class("item-box")
        self.append(self.item_box)

        item_container = Gtk.Box()
        item_container.add_css_class("item-container")
        self.item_box.append(item_container)

        icon = Gtk.Image()
        icon.set_from_paintable(load_icon_texture(result.icon or "gtk-missing-image", icon_size, self.get_scale_factor()))
        icon.add_css_class("item-icon")
        item_container.append(icon)

        self.text_container = Gtk.Box(
            width_request=int(350.0 * text_scaling_factor),
            margin_start=inner_margin_x,
            margin_end=inner_margin_x,
            orientation=Gtk.Orientation.VERTICAL,
        )
        self.text_container.set_hexpand(True)
        item_container.append(self.text_container)

        self.shortcut_label = Gtk.Label(justify=Gtk.Justification.RIGHT, width_request=44, margin_end=5)
        self.shortcut_label.add_css_class("item-shortcut")
        self.shortcut_label.add_css_class("item-text")
        self.shortcut_label.set_halign(Gtk.Align.END)
        item_container.append(self.shortcut_label)

        self.set_index(index)

        item_container.add_css_class("small-result-item")

        self.title_box = Gtk.Box()
        self.title_box.add_css_class("item-name")
        self.title_box.add_css_class("item-text")
        self.text_container.append(self.title_box)

        item_container.set_property("margin-start", outer_margin_x)
        item_container.set_property("margin-end", outer_margin_x)
        item_container.set_property("margin-top", margin_y)
        item_container.set_property("margin-bottom", margin_y)

        descr = result.get_description(query)
        if descr and not result.compact:
            descr_label = Gtk.Label(hexpand=True, max_width_chars=1, xalign=0, ellipsize=Pango.EllipsizeMode.MIDDLE)
            descr_label.add_css_class("item-descr")
            descr_label.add_css_class("item-text")
            descr_label.set_text(unescape(descr))
            self.text_container.append(descr_label)
        self.highlight_name()

    def set_index(self, index: int) -> None:
        """
        Set index for the item and assign shortcut
        """
        jump_keys = get_settings().get_jump_keys()
        if index < len(jump_keys):
            self.index = index
            self.shortcut_label.set_text(f"Alt+{jump_keys[index]}")

    def select(self) -> None:
        self.item_box.add_css_class("selected")
        self.scroll_to_focus()

    def deselect(self) -> None:
        self.item_box.remove_css_class("selected")

    def scroll_to_focus(self) -> None:
        viewport: Gtk.Viewport = self.get_ancestor(Gtk.Viewport)  # type: ignore[assignment]
        if viewport is None:
            return
        viewport_height = viewport.get_height()
        scroll_y = viewport.get_vadjustment().get_value()

        # Get widget allocation (still works in GTK4, though deprecated)
        allocation = self.get_allocation()
        widget_y = allocation.y
        widget_height = allocation.height
        bottom = widget_y + widget_height

        if scroll_y > widget_y:  # Scroll up if the widget is above visible area
            viewport.get_vadjustment().set_value(widget_y)
        elif viewport_height + scroll_y < bottom:  # Scroll down if the widget is below visible area
            viewport.get_vadjustment().set_value(bottom - viewport_height)

    def highlight_name(self) -> None:
        highlightable_input = self.result.get_highlightable_input(self.query)
        if highlightable_input and (self.result.searchable or self.result.highlightable):
            labels = []

            for label_text, is_highlight in highlight_text(highlightable_input, self.result.name):
                ellipsize_min = (not is_highlight and ELLIPSIZE_MIN_LENGTH) or ELLIPSIZE_FORCE_AT_LENGTH
                ellipsize = Pango.EllipsizeMode.MIDDLE if len(label_text) > ellipsize_min else Pango.EllipsizeMode.NONE
                label = Gtk.Label(label=unescape(label_text), ellipsize=ellipsize)
                if is_highlight:
                    label.add_css_class("item-highlight")
                labels.append(label)
        else:
            labels = [Gtk.Label(label=self.result.name, ellipsize=Pango.EllipsizeMode.MIDDLE)]

        for label in labels:
            self.title_box.append(label)

    def on_click(self, gesture: Gtk.GestureClick, _n_press: int, _x: float, _y: float) -> None:
        window = self.get_root()
        window.select_result(self.index)  # type: ignore[attr-defined]
        alt = gesture.get_current_button() != 1  # right click
        result = window.results_nav.activate(self.query, alt=alt)  # type: ignore[attr-defined]
        if result is False:
            window.hide_and_clear_input()  # type: ignore[attr-defined]
        elif result is not None:
            window.handle_event(result)  # type: ignore[attr-defined]

    def on_mouse_hover(self, _controller: Gtk.EventControllerMotion, _x: float, _y: float) -> None:
        # GTK4: Simplified mouse hover handling
        # In GTK4, the motion controller is more reliable for mouse events
        # so we don't need to check the device source
        self.get_root().select_result(self.index)  # type: ignore[attr-defined]
