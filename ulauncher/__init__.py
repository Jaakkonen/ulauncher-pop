# Eventually switch to define the version/gi_versions in pyproject.toml? see PR 1312

__version__ = "6.0.0-beta6"
version = __version__  # Keep for backwards compatibility
gi_versions = {
    "Gtk": "4.0",
    "Gdk": "4.0",
    # "GdkX11": "4.0",
    "GdkPixbuf": "2.0",
    "Pango": "1.0",
}

# this namespace module is the only way we can pin gi versions globally,
# but we also use it when we build, then we don't want to require gi
try:
    import gi

    gi.require_versions(gi_versions)
except ModuleNotFoundError:
    pass
