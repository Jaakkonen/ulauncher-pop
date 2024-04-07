from typing import Literal, NotRequired, TypedDict

from ulauncher.modes.poplauncher.jsonproto import JsonProtocol, Msg


class PopRequest(JsonProtocol):
    class Activate(Msg, int):
        ...

    class ActivateContext(Msg.obj):
        id: int
        context: int

    class Complete(Msg, int):
        ...

    class Context(Msg, int):
        ...

    class Quit(Msg, int):
        ...

    class Search(Msg, str):
        ...


TPopRequest = PopRequest.Activate | PopRequest.ActivateContext | PopRequest.Complete | PopRequest.Context | PopRequest.Quit | PopRequest.Search

class _IconSourceName(TypedDict):
    Name: str


class _IconSourceMime(TypedDict):
    Mime: str


class SearchResult(TypedDict):
    id: int
    name: str
    description: str
    icon: NotRequired[_IconSourceName | _IconSourceMime]
    category_icon: NotRequired[_IconSourceName | _IconSourceMime]
    window: NotRequired[tuple[int, int]]


class ContextOption(TypedDict):
    id: int
    name: str


class PopResponse(JsonProtocol):
    class Close(Msg):
        ...

    class Context(Msg.obj):
        id: int
        options: list[ContextOption]

    class DesktopEntry(Msg.obj):
        """
        Payload data of the DesktopEntry response (requesting client to launch a .desktop file)

        Attributes:

        path: str - The path to the .desktop file
        gpu_preference: "Default" | "NonDefault" - The GPU preference to use when launching the application
        https://specifications.freedesktop.org/desktop-entry-spec/desktop-entry-spec-latest.html#desktop-file-keywords
        "If true, the application prefers to be run on a more powerful discrete GPU if available,
        which we describe as “a GPU other than the default one” in this spec to avoid the need to
        define what a discrete GPU is and in which cases it might be considered more powerful than
        the default GPU. This key is only a hint and support might not be present depending on the implementation."

        Default: Use integrated GPU or whatever is the default GPU
        NonDefault: Use a more powerful GPU if available (it can also be the default GPU)
        """

        path: str
        gpu_preference: Literal["Default", "NonDefault"]
        action_name: str | None = None

    class Update(Msg, list[SearchResult]):
        ...

    class Fill(Msg, str):
        ...

TPopResponse = PopResponse.Close | PopResponse.Context | PopResponse.DesktopEntry | PopResponse.Update | PopResponse.Fill

if __name__ == "__main__":
    assert PopResponse.from_json('"Close"').to_json() == '"Close"'
    assert (
        PopResponse.from_json('{"Update": [{"id": 1, "name": "name", "description": "desc"}]}').to_json()
        == '{"Update": [{"id": 1, "name": "name", "description": "desc"}]}'
    )
    assert (
        PopResponse.from_json('{"Context": {"id": 1, "options": [{"id": 1, "name": "name"}]}}').to_json()
        == '{"Context": {"id": 1, "options": [{"id": 1, "name": "name"}]}}'
    )
    assert (
        PopResponse.from_json('{"DesktopEntry": {"path": "path", "gpu_preference": "Default"}}').to_json()
        == '{"DesktopEntry": {"path": "path", "gpu_preference": "Default"}}'
    )
    assert PopResponse.from_json('{"Fill": "str"}').to_json() == '{"Fill": "str"}'
    assert PopRequest.from_json('{ "Activate": 1 }').to_json() == '{"Activate": 1}'
    assert (
        PopRequest.from_json('{ "ActivateContext": { "id": 1, "context": 1 } }').to_json()
        == '{"ActivateContext": {"id": 1, "context": 1}}'
    )
    assert PopRequest.from_json('{ "Complete": 1 }').to_json() == '{"Complete": 1}'
    assert PopRequest.from_json('{ "Context": 1 }').to_json() == '{"Context": 1}'
