from typing import Any, Callable, TypedDict

IdxSpanResult = TypedDict(
    "IdxSpanResult",
    {
        "offset": list[int],
        "span": list[tuple[int, int]],
    },
)


CommandProps = TypedDict(
    "CommandProps",
    {
        "func": Callable[..., Any],
        "props": dict[str, dict[str, Any]],
    },
)
