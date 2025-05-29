from __future__ import annotations

import logging
from types import SimpleNamespace

from gi.repository import Gdk, Gtk

logger = logging.getLogger()
footer_notice = "Be aware that keyboard shortcuts may be reserved by, or conflict with your system."

RESPONSES = SimpleNamespace(OK=-5, CLOSE=-7)

MODIFIERS = (
    "Alt_L",
    "Alt_R",
    "Shift_L",
    "Shift_R",
    "Control_L",
    "Control_R",
    "Super_L",
)


class HotkeyDialog(Gtk.MessageDialog):
    _hotkey = ""

    def __init__(self):
        super().__init__(title="Set new hotkey", flags=Gtk.DialogFlags.MODAL)  # type: ignore[call-arg]
        self.add_buttons("Close", Gtk.ResponseType.CLOSE, "Save", Gtk.ResponseType.OK)
        self.set_response_sensitive(RESPONSES.OK, False)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, margin_start=10, margin_end=10)
        self._hotkey_input = Gtk.Entry(editable=False)
        vbox.append(self._hotkey_input)
        vbox.append(Gtk.Label(use_markup=True, label=f"<i><small>{footer_notice}</small></i>"))
        self.get_content_area().set_child(vbox)

        self.connect("response", self.handle_response)
        key_controller = Gtk.EventControllerKey()
        key_controller.connect("key-pressed", self.on_key_press)
        self.add_controller(key_controller)

    def handle_response(self, _widget: HotkeyDialog, response_id: int) -> None:
        if response_id == RESPONSES.OK:
            self.save_and_close()
        if response_id == RESPONSES.CLOSE:
            self.close()

    def set_hotkey(self, key_name=""):
        label = Gtk.accelerator_get_label(*Gtk.accelerator_parse(key_name))
        self._hotkey = key_name
        self._hotkey_input.set_text(label)
        self._hotkey_input.set_position(-1)
        self.set_response_sensitive(RESPONSES.OK, bool(key_name))

    def close(self):
        self._hotkey = ""
        self.hide()

    def save_and_close(self):
        self.hide()

    def on_key_press(self, controller: Gtk.EventControllerKey, keyval: int, keycode: int, state: Gdk.ModifierType) -> bool:
        key_name = Gtk.accelerator_name(keyval, state)
        label = Gtk.accelerator_get_label(keyval, state)
        breadcrumb = label.split("+")

        # treat Enter w/o modifiers as "submit"
        if self._hotkey and key_name == "Return":
            self.save_and_close()
            return True

        if self._hotkey and key_name == "BackSpace":
            self.set_hotkey()
            return True

        # Must have at least one modifier (meaning two parts) and the last part must not be one
        if len(breadcrumb) > 1 and breadcrumb[-1] not in MODIFIERS:
            self.set_hotkey(key_name)
            return True

        return False

    def run(self):
        super().run()
        return self._hotkey
