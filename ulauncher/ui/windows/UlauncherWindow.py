from __future__ import annotations

import logging
import subprocess
from typing import Any

from gi.repository import Gdk, Gtk

from ulauncher.api.result import Result
from ulauncher.config import PATHS
from ulauncher.modes.apps import AppResult
from ulauncher.modes.apps.launch_app import launch_app
from ulauncher.modes.extensions.DeferredResultRenderer import DeferredResultRenderer
from ulauncher.modes.extensions.ExtensionSocketServer import ExtensionSocketServer
from ulauncher.modes.PopLauncher import PopLauncherProvider
from ulauncher.modes.poplauncher.poplauncher_ipc import PopResponse, TPopResponse
from ulauncher.modes.shortcuts.run_script import run_script
from ulauncher.ui import LayerShell
from ulauncher.ui.ItemNavigation import ItemNavigation
from ulauncher.ui.ResultWidget import ResultWidget
from ulauncher.utils.launch_detached import open_detached
from ulauncher.utils.load_icon_surface import load_icon_surface
from ulauncher.utils.Settings import Settings
from ulauncher.utils.Theme import Theme
from ulauncher.utils.wm import get_monitor

logger = logging.getLogger()





class UlauncherWindow(Gtk.ApplicationWindow):
    _css_provider = None
    results_nav = None
    is_dragging = False
    layer_shell_enabled = False
    settings = Settings.load()
    _result_provider: PopLauncherProvider # ResultProvider

    def handle_event(self: UlauncherWindow, event: bool | list | str | dict[str, Any] | TPopResponse) -> None:  # noqa: PLR0912
        """
        Handles event from mode or extension.

        bool -> if False, hide window
        list -> list of Result instances. Keeps window open
        str -> set query text. Keeps window open

        dict -> custom events.
            type="action:open" -> opens file with xdg-open. Closes window
            type="action:clipboard_store" -> stores data in clipboard. Closes window 2 times :D
            type="action:legacy_run_script" -> runs script. Closes window
            type="action:legacy_run_many" -> runs multiple actions. Keeps window open if any action returns True
            type="event:activate_custom" -> activates custom controller. Keeps window open if keep_app_open is True
            type="event:..." -> activates extension controller. Keeps window open if keep_app_open is True
        """
        match event:
            case PopResponse.Close():
                self.hide_and_clear_input()
            case PopResponse.Context(id=id, options=options):
                raise NotImplementedError("Context options are not implemented")
            case PopResponse.DesktopEntry(path, gpu_preference, action_name):
                # Launch the .desktop file
                launch_app(path.rsplit('/',1)[1])
            case PopResponse.Update(l):
                def make_on_enter(id):
                    def on_enter(query):
                        self._result_provider.on_enter(id)
                    return on_enter
                res = [
                    Result(
                        name=r['name'],
                        description=r['description'],
                        icon=r.get('icon', {}).get('Name', ''),
                        on_enter=make_on_enter(r['id'])
                    )
                    for r in l
                ]
                self.show_results(res)
            case PopResponse.Fill(txt):
                # Replace the current query with the given text
                self.app.query = txt
            case _ as x:
                raise ValueError(f"Invalid result from mode: {type(event).__name__}")

    def __init__(self, **kwargs):
        super().__init__(
            decorated=False,
            deletable=False,
            has_focus=True,
            icon_name="ulauncher",
            resizable=False,
            skip_pager_hint=True,
            skip_taskbar_hint=True,
            title="Ulauncher - Application Launcher",
            urgency_hint=True,
            window_position=Gtk.WindowPosition.CENTER,
            **kwargs,
        )
        self._result_provider = PopLauncherProvider(self.handle_event)

        if LayerShell.is_supported():
            self.layer_shell_enabled = LayerShell.enable(self)

        # This box exists only for setting the margin conditionally, based on ^
        # without the theme being able to override it
        self.window_frame = Gtk.Box()
        self.add(self.window_frame)

        window_container = Gtk.Box(app_paintable=True, orientation=Gtk.Orientation.VERTICAL)
        self.window_frame.pack_start(window_container, True, True, 0)

        event_box = Gtk.EventBox()
        input_box = Gtk.Box()
        event_box.add(input_box)

        self.input = Gtk.Entry(
            can_default=True,
            can_focus=True,
            has_focus=True,
            is_focus=True,
            height_request=30,
            margin_top=15,
            margin_bottom=15,
            margin_start=20,
            margin_end=20,
            receives_default=True,
        )

        prefs_btn = Gtk.Button(
            name="prefs_btn",
            width_request=24,
            height_request=24,
            receives_default=False,
            halign=Gtk.Align.CENTER,
            valign=Gtk.Align.CENTER,
            margin_end=15,
        )

        input_box.pack_start(self.input, True, True, 0)
        input_box.pack_end(prefs_btn, False, False, 0)

        self.scroll_container = Gtk.ScrolledWindow(
            can_focus=True,
            max_content_height=500,
            hscrollbar_policy=Gtk.PolicyType.NEVER,
            propagate_natural_height=True,
            shadow_type=Gtk.ShadowType.IN,
        )
        self.result_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.scroll_container.add(self.result_box)

        window_container.pack_start(event_box, True, True, 0)
        window_container.pack_end(self.scroll_container, True, True, 0)

        window_container.get_style_context().add_class("app")
        self.input.get_style_context().add_class("input")
        prefs_btn.get_style_context().add_class("prefs-btn")
        self.result_box.get_style_context().add_class("result-box")

        prefs_icon_surface = load_icon_surface(f"{PATHS.ASSETS}/icons/gear.svg", 16, self.get_scale_factor())
        prefs_btn.set_image(Gtk.Image.new_from_surface(prefs_icon_surface))
        self.window_frame.show_all()

        self.connect("focus-in-event", self.on_focus_in)
        self.connect("focus-out-event", self.on_focus_out)
        event_box.connect("button-press-event", self.on_mouse_down)
        self.connect("button-release-event", self.on_mouse_up)
        self.input.connect("changed", self.on_input_changed)
        self.input.connect("key-press-event", self.on_input_key_press)
        prefs_btn.connect("clicked", lambda *_: self.app.show_preferences())

        self.set_keep_above(True)
        self.position_window()

        # this will trigger to show frequent apps if necessary
        self.show_results([])
        assert self.app is not None

    ######################################
    # GTK Signal Handlers
    ######################################

    def on_focus_out(self, *_):
        if not self.is_dragging:
            self.hide()

    def on_focus_in(self, *_args):
        if self.settings.grab_mouse_pointer:
            ptr_dev = self.get_pointer_device()
            result = ptr_dev.grab(
                self.get_window(), Gdk.GrabOwnership.NONE, True, Gdk.EventMask.ALL_EVENTS_MASK, None, 0
            )
            logger.debug("Focus in event, grabbing pointer: %s", result)

    def on_input_changed(self, _):
        """
        Triggered by user input
        """
        self.app._query = self.input.get_text().lstrip()  # noqa: SLF001
        if self.is_visible():
            # input_changed can trigger when hiding window
            self._result_provider.on_query_change(self.app.query)

    def on_input_key_press(self, entry_widget: Gtk.Entry, event: Gdk.EventKey) -> bool:  # noqa: PLR0911, PLR0912
        """
        Triggered by user key press
        Return True to stop other handlers from being invoked for the event
        """
        keyname = Gdk.keyval_name(event.keyval)
        alt = bool(event.state & Gdk.ModifierType.MOD1_MASK)
        ctrl = bool(event.state & Gdk.ModifierType.CONTROL_MASK)
        jump_keys = self.settings.get_jump_keys()

        if len(self.settings.arrow_key_aliases) == 4:  # noqa: PLR2004
            left_alias, down_alias, up_alias, right_alias = [*self.settings.arrow_key_aliases]  # type: ignore[misc]
        else:
            left_alias, down_alias, up_alias, right_alias = [None] * 4
            logger.warning(
                "Invalid value for arrow_key_aliases: %s, expected four letters", self.settings.arrow_key_aliases
            )

        if keyname == "Escape":
            self.hide()
            return True

        if self.results_nav:
            if keyname in ("Up", "ISO_Left_Tab") or (ctrl and keyname == up_alias):
                self.results_nav.go_up()
                return True

            if keyname in ("Down", "Tab") or (ctrl and keyname == down_alias):
                self.results_nav.go_down()
                return True

            if ctrl and keyname == left_alias:
                entry_widget.set_position(max(0, entry_widget.get_position() - 1))
                return True

            if ctrl and keyname == right_alias:
                entry_widget.set_position(entry_widget.get_position() + 1)
                return True

            if keyname in ("Return", "KP_Enter"):
                result = self.results_nav.activate(self.app.query, alt=alt)
                if result is False:
                    self.hide_and_clear_input()
                return True
            if alt and event.string in jump_keys:
                self.select_result(jump_keys.index(event.string))
                return True
        return False

    def on_mouse_down(self, _event_box: Gtk.EventBox, event: Gdk.EventButton) -> None:
        """
        Move the window on drag
        """
        if event.button == 1 and event.type == Gdk.EventType.BUTTON_PRESS:
            self.is_dragging = True
            self.begin_move_drag(event.button, int(event.x_root), int(event.y_root), event.time)

    def on_mouse_up(self, *_):
        self.is_dragging = False

    ######################################
    # Helpers
    ######################################

    @property
    def app(self):
        return self.get_application()

    def apply_css(self, widget: Gtk.Widget) -> None:
        assert self._css_provider
        Gtk.StyleContext.add_provider(
            widget.get_style_context(), self._css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
        if isinstance(widget, Gtk.Container):
            widget.forall(self.apply_css)

    def apply_theme(self):
        if not self._css_provider:
            self._css_provider = Gtk.CssProvider()
        theme_css = Theme.load(self.settings.theme_name).get_css().encode()
        self._css_provider.load_from_data(theme_css)
        self.apply_css(self)
        visual = self.get_screen().get_rgba_visual()
        if visual:
            self.set_visual(visual)

    def position_window(self):
        # Try setting a transparent background
        screen = self.get_screen()
        visual = screen.get_rgba_visual()
        shadow_size = 20 if visual else 0
        self.window_frame.set_properties(
            margin_top=shadow_size,
            margin_bottom=shadow_size,
            margin_start=shadow_size,
            margin_end=shadow_size,
        )
        if visual is None:
            logger.info("Screen does not support alpha channels. Likely not running a compositor.")
            visual = screen.get_system_visual()

        self.set_visual(visual)
        self.apply_theme()

        monitor = get_monitor(self.settings.render_on_screen != "default-monitor")
        if monitor:
            geo = monitor.get_geometry()
            max_height = geo.height - (geo.height * 0.15) - 100  # 100 is roughly the height of the text input
            window_width = self.settings.base_width
            pos_x = int(geo.width * 0.5 - window_width * 0.5 + geo.x)
            pos_y = int(geo.y + geo.height * 0.12)
            self.set_property("width-request", window_width)
            self.scroll_container.set_property("max-content-height", max_height)

            if self.layer_shell_enabled:
                LayerShell.set_vertical_position(self, pos_y)
            else:
                self.move(pos_x, pos_y)

    def show(self):
        self.present()
        # note: present_with_time is needed on some DEs to defeat focus stealing protection
        # (Gnome 3 forks like Cinnamon or Budgie, but not Gnome 3 itself any longer)
        # The correct time to use is the time of the user interaction requesting the focus, but we don't have access
        # to that, so we use `Gdk.CURRENT_TIME`, which is the same as passing 0.
        self.present_with_time(Gdk.CURRENT_TIME)
        self.position_window()

        if not self.app.query:
            # make sure frequent apps are shown if necessary
            self.show_results([])

        self.input.grab_focus()
        super().show()

    def hide(self, *args, **kwargs):
        """Override the hide method to ensure the pointer grab is released."""
        if self.settings.grab_mouse_pointer:
            self.get_pointer_device().ungrab(0)
        super().hide(*args, **kwargs)
        if self.settings.clear_previous_query:
            self.app.query = ""

    def select_result(self, index):
        if self.results_nav:
            self.results_nav.select(index)

    def get_pointer_device(self):
        window = self.get_window()
        assert window
        device_mapper = window.get_display().get_device_manager()
        assert device_mapper
        return device_mapper.get_client_pointer()

    def hide_and_clear_input(self):
        self.input.set_text("")
        self.hide()

    def get_default_results(self) -> list[Result]:
        return [] #AppResult.get_most_frequent(self.settings.max_recent_apps)

    def show_results(self, results: list[Result]) -> None:
        """
        :param list results: list of Result instances
        """
        self.results_nav = None
        self.result_box.foreach(lambda w: w.destroy())

        limit = len(self.settings.get_jump_keys()) or 25
        if not self.input.get_text() and self.settings.max_recent_apps:
            results = []

        if results:
            result_widgets: list[ResultWidget] = []
            for index, result in enumerate(results[:limit]):
                result_widget = ResultWidget(result, index, self.app.query)
                result_widgets.append(result_widget)
                self.result_box.add(result_widget)
            self.results_nav = ItemNavigation(result_widgets)
            self.results_nav.select_default(self.app.query)

            self.result_box.set_margin_bottom(10)
            self.result_box.set_margin_top(3)
            self.apply_css(self.result_box)
            self.scroll_container.show_all()
        else:
            # Hide the scroll container when there are no results since it normally takes up a
            # minimum amount of space even if it is empty.
            self.scroll_container.hide()
        logger.debug("render %s results", len(results))
