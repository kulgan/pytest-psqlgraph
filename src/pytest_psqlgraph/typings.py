import sys

if sys.version_info >= (3, 8):
    from typing import (  # pylint: disable=no-name-in-module
        Final,
        Literal,
        Protocol,
        TypedDict,
    )
else:
    from typing_extensions import Final, Literal, Protocol, TypedDict


__all__ = [
    "Final",
    "Literal",
    "Protocol",
    "TypedDict",
]
