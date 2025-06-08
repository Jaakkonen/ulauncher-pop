from __future__ import annotations

import logging
from typing import Any

from gi.repository import Gdk, Gtk

from ulauncher.modes.apps.launch_app import launch_app
from ulauncher.modes.PopLauncher import PopLauncherProvider
from ulauncher.modes.poplauncher.poplauncher_ipc import PopResponse, TPopResponse
from ulauncher.modes.poplauncher.result import Result
from ulauncher.ui.ItemNavigation import ItemNavigation
from ulauncher.ui.ResultWidget import ResultWidget
from ulauncher.utils.Settings import get_settings
from ulauncher.utils.Theme import get_theme_css
from ulauncher.utils.wm import get_monitor, get_text_scaling_factor

logger = logging.getLogger()


class UlauncherWindow(Gtk.ApplicationWindow):
    _css_provider = None
    results_nav = None
    is_dragging = False
    # layer_shell_enabled = False
    settings = get_settings()
    _result_provider: PopLauncherProvider # ResultProvider

    def handle_event(self: UlauncherWindow, event: bool | list | str | dict[str, Any] | TPopResponse) -> None:
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
                launch_app(path.rsplit("/",1)[1])
            case PopResponse.Update(l):
                def make_on_enter(id):
                    def on_enter(query):
                        self._result_provider.on_enter(id)
                        return False  # Hide window after activation
                    return on_enter
                res = [
                    Result(
                        name=r["name"],
                        description=r["description"],
                        icon=r.get("icon", {}).get("Name", ""),
                        on_enter=make_on_enter(r["id"])
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
            title="Ulauncher - Application Launcher",
            **kwargs,
        )
        text_scaling_factor = get_text_scaling_factor()
        # GTK4 properties
        self.set_decorated(False)
        self.set_deletable(False)
        self.set_resizable(False)
        self.set_icon_name("ulauncher")

        self._result_provider = PopLauncherProvider(self.handle_event)

        # if LayerShell.is_supported():
        #     self.layer_shell_enabled = LayerShell.enable(self)

        # This box exists only for setting the margin conditionally, based on ^
        # without the theme being able to override it
        self.window_frame = Gtk.Box()
        self.set_child(self.window_frame)


        window_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        window_container.add_css_class("app")
        self.window_frame.append(window_container)

        # Create input box with event controllers instead of EventBox
        input_box = Gtk.Box()

        self.input = Gtk.Entry(
            height_request=30,
            width_request=int(520.0 * text_scaling_factor),
            margin_top=10,
            margin_bottom=10,
            margin_start=20,
            margin_end=20,
            activates_default=False,
        )
        self.input.add_css_class("input")

        input_box.append(self.input)

        self.scroll_container = Gtk.ScrolledWindow(
            can_focus=True,
            max_content_height=500,
            hscrollbar_policy=Gtk.PolicyType.NEVER,
            propagate_natural_height=True,
            has_frame=True,
        )
        self.result_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.result_box.add_css_class("result-box")
        self.scroll_container.set_child(self.result_box)

        window_container.append(input_box)
        window_container.append(self.scroll_container)

        self.setup_event_controllers(input_box)

        self.position_window()

        # this will trigger to show frequent apps if necessary
        self.show_results([])
        assert self.app is not None

    def setup_event_controllers(self, input_box: Gtk.Box) -> None:
        """Set up event controllers for GTK4"""

        # Focus controllers
        focus_controller = Gtk.EventControllerFocus()
        focus_controller.connect("enter", self.on_focus_in)
        focus_controller.connect("leave", self.on_focus_out)
        self.add_controller(focus_controller)

        # Mouse/drag controllers for window movement
        click_gesture = Gtk.GestureClick()
        click_gesture.connect("pressed", self.on_mouse_down)
        click_gesture.connect("released", self.on_mouse_up)
        input_box.add_controller(click_gesture)

        # Key controller for input
        key_controller = Gtk.EventControllerKey()
        key_controller.connect("key-pressed", self.on_input_key_press)
        self.input.add_controller(key_controller)

        # Input change signal
        self.input.connect("changed", self.on_input_changed)

        # Entry activate signal (handles Enter key)
        self.input.connect("activate", self.on_input_activate)


    ######################################
    # GTK Signal Handlers
    ######################################

    def on_focus_out(self, *_):
        if not self.is_dragging:
            self.hide()

    def on_focus_in(self, *_args):
        if self.settings.grab_mouse_pointer:
            # GTK4 pointer grabbing - simplified approach
            surface = self.get_surface()
            if surface:
                logger.debug("Focus in event, setting up grab")

    def on_input_changed(self, _):
        """
        Triggered by user input
        """
        self.app._query = self.input.get_text().lstrip()  # noqa: SLF001
        if self.get_visible():
            # input_changed can trigger when hiding window
            self._result_provider.on_query_change(self.app.query)

    def on_input_activate(self, _):
        """
        Triggered by user input (Enter key)
        """
        if self.results_nav:
            result = self.results_nav.activate(self.app.query, alt=False)
            if result is False:
                self.hide_and_clear_input()

    def on_input_key_press(self, _controller: Gtk.EventControllerKey, keyval: int, _keycode: int, state: Gdk.ModifierType) -> bool:
        """
        Triggered by user key press
        Return True to stop other handlers from being invoked for the event
        """
        keyname = Gdk.keyval_name(keyval)
        alt = bool(state & Gdk.ModifierType.ALT_MASK)
        ctrl = bool(state & Gdk.ModifierType.CONTROL_MASK)
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
                self.input.set_position(max(0, self.input.get_position() - 1))
                return True

            if ctrl and keyname == right_alias:
                self.input.set_position(self.input.get_position() + 1)
                return True

            if keyname in ("Return", "KP_Enter"):
                result = self.results_nav.activate(self.app.query, alt=alt)
                if result is False:
                    self.hide_and_clear_input()
                return True
            if alt and Gdk.keyval_to_unicode(keyval):
                event_string = chr(Gdk.keyval_to_unicode(keyval))
                if event_string in jump_keys:
                    self.select_result(jump_keys.index(event_string))
                    return True
        return False

    def on_mouse_down(self, gesture: Gtk.GestureClick, _n_press: int, x: float, y: float) -> None:
        """
        Move the window on drag
        """
        if gesture.get_current_button() == 1:
            self.is_dragging = True
            # GTK4 window dragging
            surface = self.get_surface()
            if surface and hasattr(surface, "begin_move_drag"):
                # Get the device from the gesture
                device = gesture.get_device()
                if device:
                    surface.begin_move_drag(
                        device,
                        gesture.get_current_button(),
                        int(x), int(y),
                        gesture.get_current_event_time()
                    )

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
        widget.get_style_context().add_provider(
            self._css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
        # GTK4: use first_child and next_sibling to iterate
        child = widget.get_first_child()
        while child:
            self.apply_css(child)
            child = child.get_next_sibling()

    def apply_theme(self):
        if not self._css_provider:
            self._css_provider = Gtk.CssProvider()
        theme_css = get_theme_css(self.settings.theme_name).encode()
        self._css_provider.load_from_data(theme_css, -1)
        self.apply_css(self)

    def position_window(self):
        # Apply theme first
        self.apply_theme()

        monitor = get_monitor(self.settings.render_on_screen != "default-monitor")
        if monitor:
            geo = monitor.get_geometry()
            max_height = geo.height - (geo.height * 0.15) - 100  # 100 is roughly the height of the text input

            self.scroll_container.set_max_content_height(max_height)

            # Set margins for shadow effect
            shadow_size = 20
            self.window_frame.set_margin_top(shadow_size)
            self.window_frame.set_margin_bottom(shadow_size)
            self.window_frame.set_margin_start(shadow_size)
            self.window_frame.set_margin_end(shadow_size)

            self.present()

            # if self.layer_shell_enabled:
            #     LayerShell.set_vertical_position(self, pos_y)
            # else:
            #     # GTK4 doesn't have move() for ApplicationWindow, use present() instead
            #     self.present()

    def show(self):
        self.present()
        self.position_window()

        if not self.app.query:
            # make sure frequent apps are shown if necessary
            self.show_results([])

        self.input.grab_focus()

    def hide(self, *args, **kwargs):
        """Override the hide method to ensure any grabs are released."""
        if self.settings.grab_mouse_pointer:
            # GTK4 simplified ungrab
            pass
        super().hide(*args, **kwargs)
        if self.settings.clear_previous_query:
            self.app.query = ""

    def select_result(self, index):
        if self.results_nav:
            self.results_nav.select(index)

    def hide_and_clear_input(self):
        self.input.set_text("")
        self.hide()

    def show_results(self, results: list[Result]) -> None:
        """
        :param list results: list of Result instances
        """
        self.results_nav = None
        # GTK4: Remove all children
        child = self.result_box.get_first_child()
        while child:
            next_child = child.get_next_sibling()
            self.result_box.remove(child)
            child = next_child

        limit = len(self.settings.get_jump_keys()) or 25
        if not self.input.get_text() and self.settings.max_recent_apps:
            results = []

        if results:
            result_widgets: list[ResultWidget] = []
            for index, result in enumerate(results[:limit]):
                result_widget = ResultWidget(result, index, self.app.query)
                result_widgets.append(result_widget)
                self.result_box.append(result_widget)
            self.results_nav = ItemNavigation(result_widgets)
            self.results_nav.select_default(self.app.query)

            self.result_box.set_margin_bottom(10)
            self.result_box.set_margin_top(0)
            self.apply_css(self.result_box)
            self.scroll_container.set_visible(True)
        else:
            # Hide the scroll container completely when empty to avoid any extra spacing
            self.scroll_container.set_visible(False)
        logger.debug("render %s results", len(results))
