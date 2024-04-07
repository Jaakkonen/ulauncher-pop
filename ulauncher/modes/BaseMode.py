from collections.abc import Iterable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ulauncher.modes.apps.AppResult import AppResult


class BaseMode:
    def is_enabled(self, _query):
        """
        Return True if mode should be enabled for a query
        """
        return False

    def on_query_change(self, _query) -> None:
        """
        Triggered when user changes a search query
        """

    def on_query_backspace(self, _query):
        """
        Return string to override default backspace and set the query to that string
        """

    def handle_query(self, _query):
        """
        :rtype: list of Results
        """
        return []

    def get_triggers(self) -> Iterable["AppResult"]:
        """
        Returns an iterable of searchable results
        """
        return []

    def get_fallback_results(self):
        """
        Returns a list of fallback results to
        be displayed if nothing matches the user input
        """
        return []
