from collections.abc import Iterable
from typing import Protocol


class Positioned(Protocol):
    position: int


def by_position[Item: Positioned](items: Iterable[Item]) -> list[Item]:
    return sorted(items, key=lambda item: item.position)


def renumber[Item: Positioned](
    items: Iterable[Item], moved: Item | None = None, index: int = 0
) -> list[Item]:
    """Rewrite positions as 0..n-1, optionally placing `moved` at `index`."""
    ordered = by_position(item for item in items if item is not moved)
    if moved is not None:
        ordered.insert(max(0, min(index, len(ordered))), moved)
    for position, item in enumerate(ordered):
        item.position = position
    return ordered
