from __future__ import annotations

import logging
from functools import cache

from gi.repository import Gio, Gtk

from ulauncher.config import APP_ID
from ulauncher.ui.windows.UlauncherWindow import UlauncherWindow

logger = logging.getLogger()


class UlauncherApp(Gtk.Application):
    """
    Main Ulauncher application (singleton)
    """

    # Gtk.Applications check if the app is already registered and if so,
    # new instances sends the signals to the registered one
    # So all methods except __init__ runs on the main app
    _query = ""
    window: UlauncherWindow | None = None

    @classmethod
    @cache
    def get_instance(cls):
        return cls()

    def __init__(self, *args, **kwargs):
        kwargs.update(application_id=APP_ID, flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE)
        super().__init__(*args, **kwargs)
        self.connect("startup", self.setup)  # runs only once on the main instance

    @property
    def query(self) -> str:
        return self._query

    @query.setter
    def query(self, value: str) -> None:
        self._query = value.lstrip()
        if self.window:
            self.window.input.set_text(self._query)
            self.window.input.set_position(-1)

    def do_startup(self):
        Gtk.Application.do_startup(self)
        Gio.ActionMap.add_action_entries(
            self, [("set-query", self.activate_query, "s")]
        )

    def do_activate(self, *_args, **_kwargs):
        self.show_launcher()

    def do_command_line(self, *args, **_kwargs):
        # We need to use "--no-window" from the unique CLI invocation here,
        # Can't use config.get_options(), because that's the daemon's initial cli arguments
        if "--no-window" not in args[0].get_arguments():
            self.activate()

        return 0

    def setup(self, _):
        self.hold()  # Keep the app running even without a window

    def show_launcher(self):
        if not self.window:
            self.window = UlauncherWindow(application=self)
        self.window.show()

    def activate_query(self, _action, variant, *_):
        self.activate()
        self.query = variant.get_string()

