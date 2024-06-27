import logging
import os
import sys

from gi.repository import GLib

logger = logging.getLogger()


def detach_child():
    """
    A utility function which runs in the child process launched by spawn_async
    and before execing the supplied command.
    """
    # Use setsid to take "session leader" status so that the child pid is
    # definitely detached from the parent ulauncher process
    os.setsid()

    # Don't redirect the standard file descriptors unless connected to a terminal.
    if not sys.stdout.isatty():
        return

    # Reopen the stdin, stdout, and stderr file descriptors to /dev/null. This
    # ensures the stdout/stderr are no longer connected to the terminal. This
    # serves a similar purpose as the standard "nohup" command. Any processes
    # connected to the terminal will get the interrupt signal when "Ctrl-C" is
    # called, so this redirection prevents the child process from exiting when
    # ulauncher is interrupted. Unlike "nohup", stdout and stderr are not sent
    # to a file but sent to /dev/null instead.
    null_fp = open("/dev/null", "w+b")  # noqa: SIM115
    null_fd = null_fp.fileno()
    for fp in [sys.stdin, sys.stdout, sys.stderr]:
        orig_fd = fp.fileno()
        fp.close()
        os.dup2(null_fd, orig_fd)

USE_SYSTEMD_RUN = False
def launch_detached(cmd):

    if USE_SYSTEMD_RUN:
        cmd = ["systemd-run", "--user", "--scope", *cmd]


    env = dict(os.environ.items())
    # Make sure GDK apps aren't forced to use x11 on wayland due to ulauncher's need to run
    # under X11 for proper centering.
    if env.get("GDK_BACKEND") != "wayland":
        env.pop("GDK_BACKEND", None)

    try:
        envp = [f"{k}={v}" for k, v in env.items()]
        logger.debug("Launching detached: %s", cmd)
        GLib.spawn_async(
            argv=cmd,
            envp=envp,
            flags=GLib.SpawnFlags.SEARCH_PATH_FROM_ENVP | GLib.SpawnFlags.SEARCH_PATH,
            child_setup=None if USE_SYSTEMD_RUN else detach_child,
        )
    except Exception:
        logger.exception('Could not launch "%s"', cmd)


def open_detached(path_or_url):
    launch_detached(["xdg-open", path_or_url])
