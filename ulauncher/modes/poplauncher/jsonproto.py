"""
Helper classes for defining a JSON protocol with message classes with serialization.

TODO:
* Make the JsonProtocol a enum type such that it can be used as a type hint.
  - Requires https://github.com/python/typing/pull/1591 to be accepted and implemented in Pyright/MyPy.
"""

import json
from dataclasses import asdict, dataclass, is_dataclass
from typing import (
    dataclass_transform,
)


class JsonProtocol:
    """
    Usage:
        Extend this class and define subclasses with the message name and the message payload.
        Those are registered to the parent class cls._msg_registry[name] = msgsubclass
        and instantiated with the payload data.

        class MyProtocol(JsonProtocol):
            class MyMessage(Msg):
                payload: str
            class IntMessage(Msg, int): ...

        msg = MyProtocol.from_json('{"MyMessage": {"payload": "data"}}')
        assert isinstance(msg, MyProtocol.MyMessage)
        assert msg.payload == "data"
        assert msg.to_json() == '{"MyMessage": {"payload": "data"}}'
        intmsg = MyProtocol.from_json('{"IntMessage": 1}')
        assert isinstance(intmsg, MyProtocol.IntMessage)
        assert intmsg == 1
        assert intmsg.to_json() == '{"IntMessage": 1}'
    """

    def __init_subclass__(cls) -> None:
        cls._msg_registry = {
            name: subcls
            for name, subcls in cls.__dict__.items()
            if isinstance(subcls, type) and issubclass(subcls, _Msg)
        }

    @classmethod
    def from_json(cls, data: str) -> "Msg":
        try:
            obj = json.loads(data)
        except json.JSONDecodeError as e:
            err = f"Error decoding JSON: {e}"
            e.add_note(f"Data: {data}")
            raise ValueError(err) from e
        classname = None
        args = []
        kwargs = {}
        # Expect data to be dict with one key
        if isinstance(obj, dict):
            if len(obj) != 1:
                err = f"Expected a dict with one string key, got {obj}"
                raise ValueError(err)
            classname, value = next(iter(obj.items()))
            if isinstance(value, dict):
                kwargs = value
            else:
                args = [value]
        elif isinstance(obj, str):
            classname = obj
        else:
            err = f"Expected a dict or string, got {obj}"
            raise TypeError(err)

        msgreg = getattr(cls, "_msg_registry", None)
        if msgreg is None:
            err = f"Class {cls.__name__} is not a JsonProtocol, it doesn't have a _msg_registry"
            raise ValueError(err)
        if classname not in msgreg:
            err = f'Cannot deserialize, didn\'t find subclass for "{key}". Expected one of {list(msgreg.keys())}'
            raise ValueError(err)
        try:
            return msgreg[classname](*args, **kwargs)
        except TypeError as e:
            err = f"Error instantiating {classname} with args={args} kwargs={kwargs}: {e}"

            raise ValueError(err)


_OVERRIDE_MSG_SUBCLASSES = False


class MsgMeta(type):
    def __new__(cls, name, bases, ns, **kwds):
        subcls = super().__new__(cls, name, bases, ns, **kwds)
        # If the only base is "Msg" make it a dataclass
        if _OVERRIDE_MSG_SUBCLASSES:
            if Msg.obj in bases:
                subcls = dataclass(subcls)
            else:
                # For non-dataclass subclasses override __repr__
                orig_repr = subcls.__repr__
                if orig_repr is object.__repr__:
                    def orig_repr(self):
                        return ""

                def __repr__(self):
                    return f"{self.__class__.__qualname__}({orig_repr(self)})"

                subcls.__repr__ = __repr__
                if getattr(subcls, "__str__", None) is not None:
                    subcls.__str__ = subcls.__repr__

        return subcls


class _Msg(metaclass=MsgMeta):
    def to_json(self) -> str:
        classname = type(self).__name__
        if is_dataclass(self):
            data = asdict(self)
            ser = {classname: data}
        elif isinstance(self, str | int | float | list):
            ser = {classname: self}
        elif type(self).__bases__ == (Msg,):
            ser = classname
        else:
            err = f"Cannot serialize {self}"
            raise ValueError(err)
        return json.dumps(ser)


class Msg(_Msg):
    @dataclass_transform()
    class obj(_Msg):
        ...


_OVERRIDE_MSG_SUBCLASSES = True

__all__ = ["JsonProtocol", "Msg"]
