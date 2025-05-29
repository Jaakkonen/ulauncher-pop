from __future__ import annotations
from dataclasses import dataclass

from typing import Any

from ulauncher.api.shared.query import Query


DEFAULT_ACTION = True  #  keep window open and do nothing

@dataclass
class Result:
    on_enter: Any
    searchable: bool = False
    compact: bool = False
    highlightable: bool = False
    name: str = ""
    description: str = ""
    keyword: str = ""
    icon: str = ""
    context: tuple[ResultContext, ...] = ()

    def get_highlightable_input(self, query: Query) -> str | None:
        if self.keyword and self.keyword == query.keyword:
            return query.argument
        return str(query)


    def on_activation(self, query: Query, alt: bool = False) -> Any:
        """
        Handle the main action
        """
        handler = getattr(self, "on_alt_enter" if alt else "on_enter", DEFAULT_ACTION)
        return handler(query) if callable(handler) else handler

    def get_description(self, _: Query) -> str:
        return self.description


@dataclass
class ResultContext:
    id: int
    name: str
