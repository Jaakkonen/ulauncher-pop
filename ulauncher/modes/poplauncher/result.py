from __future__ import annotations

from dataclasses import dataclass
from typing import Any

DEFAULT_ACTION = True  #  keep window open and do nothing

@dataclass
class Result:
    on_enter: Any
    # Controls whether the title will be highligthed based on the query.
    searchable: bool = True
    compact: bool = False
    highlightable: bool = False
    name: str = ""
    description: str = ""
    # keyword: str = ""
    icon: str = ""
    # context: tuple[ResultContext, ...] = ()

    def get_highlightable_input(self, query: str) -> str | None:
        # if self.keyword and self.keyword == query.keyword:
        #     return query.argument
        return str(query)


    def on_activation(self, query: str, alt: bool = False) -> Any:
        """
        Handle the main action
        """
        handler = getattr(self, "on_alt_enter" if alt else "on_enter", DEFAULT_ACTION)
        return handler(query) if callable(handler) else handler

    def get_description(self, _query: str) -> str:
        return self.description
