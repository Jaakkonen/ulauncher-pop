import logging

from gi.repository import Gdk, Gio

logger = logging.getLogger()


def launch_app(desktop_entry_name: str, uris=None):
    """
    Launch an application using its desktop entry name.

    Args:
        desktop_entry_name: The desktop file name (with or without .desktop suffix)
        uris: Optional list of URIs to pass as arguments to the application

    Returns:
        bool: True if launch was successful, False otherwise
    """
    try:
        # Handle desktop file name - add .desktop suffix if not present
        if desktop_entry_name.endswith(".desktop"):
            desktop_file_name = desktop_entry_name
        else:
            desktop_file_name = f"{desktop_entry_name}.desktop"

        # Create DesktopAppInfo from the desktop file
        app_info = Gio.DesktopAppInfo.new(desktop_file_name)

        if not app_info:
            logger.error(f"No such application: {desktop_entry_name}")
            return False

        # Prepare URI list if provided
        file_list = None
        if uris:
            file_list = []
            for uri in uris:
                file_obj = Gio.File.new_for_commandline_arg(uri)
                file_list.append(file_obj)

        # Get the default display and create launch context
        display = Gdk.Display.get_default()
        launch_context = display.get_app_launch_context() if display else Gio.AppLaunchContext()

        # Launch the application
        success = app_info.launch(file_list, launch_context)

        if not success:
            logger.error(f"Failed to launch application: {desktop_entry_name}")
            return False

        logger.info(f"Successfully launched application: {desktop_entry_name}")
        return True

    except Exception as e:
        logger.error(f"Error launching application {desktop_entry_name}: {e}")
        return False
