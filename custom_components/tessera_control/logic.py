"""Decisions of Tessera Control, free of Home Assistant so they can be tested alone."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field

PRESENT_STATES = frozenset({"on", "home"})

# The situations the brightness follows; each gets one of the levels
DAY = "day"
EVENING = "evening"
DARK = "dark"
AWAY = "away"
ASLEEP = "asleep"


@dataclass(frozen=True)
class PageRule:
    """When a page belongs to the rotation."""

    page: int
    always: bool
    entity_id: str | None = None
    states: frozenset[str] = field(default_factory=frozenset)

    def applies(self, states: Mapping[str, str | None]) -> bool:
        """Return True when the page belongs to the rotation now."""
        if self.always:
            return True
        if self.entity_id is None:
            return False
        return states.get(self.entity_id) in self.states


def active_pages(
    rules: Iterable[PageRule], states: Mapping[str, str | None], fallback: int
) -> list[int]:
    """Pages in the rotation, in order; the fallback page when none applies."""
    pages = sorted({rule.page for rule in rules if rule.applies(states)})
    return pages or [fallback]


def page_after(pages: Sequence[int], current: int | None) -> int:
    """The page that follows the current one, round and round."""
    if current in pages:
        return pages[(pages.index(current) + 1) % len(pages)]
    return pages[0]


def page_after_change(
    before: Sequence[int], after: Sequence[int], current: int | None
) -> int:
    """The page to show when the list of pages changed.

    A page that joined shows at once (the last one when several joined); when the
    current page left, the first page; otherwise the current page stays.
    """
    joined = [page for page in after if page not in before]
    if before and joined:
        return joined[-1]
    if current in after:
        return current
    return after[0]


def is_present(state: str | None) -> bool:
    """A presence entity says someone is home: on, home, or a count above 0."""
    if state is None:
        return False
    if state in PRESENT_STATES:
        return True
    try:
        return float(state) > 0
    except ValueError:
        return False


def is_lit(states: Iterable[str | None]) -> bool:
    """At least one of the lights is on. Unavailable lights count as off."""
    return any(state == "on" for state in states)


def situation(*, asleep: bool, present: bool, sun_up: bool, room_lit: bool) -> str:
    """The situation the brightness follows; the first rule that fits wins."""
    if asleep:
        return ASLEEP
    if not present:
        return AWAY
    if not sun_up:
        return EVENING if room_lit else DARK
    return DAY
