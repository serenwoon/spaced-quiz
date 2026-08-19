"""간격 반복 — SM-2 변형.

원본 SM-2와 한 군데 다르다. 「애매」에서 간격을 늘리지 않고 **그대로 둔다.**
퀴즈 노트가 스스로 적어둔 기준이 그렇기 때문이다 —

    답을 펼쳤을 때 "아 맞다"가 아니라 "아 그렇구나"면 못 맞힌 것이다.

「아 맞다」는 떠올랐다는 뜻이고 「아 그렇구나」는 못 떠올렸다는 뜻이다. 후자를
맞은 것으로 쳐서 간격을 늘리면, 다음에 만날 때는 더 못 떠오른다.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date, timedelta

WRONG, VAGUE, RIGHT = 1, 2, 3
LABEL = {WRONG: "틀림", VAGUE: "애매", RIGHT: "맞음"}

EASE_START = 2.5
EASE_FLOOR = 1.3
FIRST, SECOND = 1, 6


@dataclass(frozen=True)
class State:
    interval: int = 0
    reps: int = 0
    ease: float = EASE_START
    due: date | None = None
    last: date | None = None
    grade: int = 0

    @property
    def seen(self) -> bool:
        return self.last is not None


def grade(state: State, score: int, today: date) -> State:
    """채점 하나를 반영한 다음 상태."""
    if score == WRONG:
        interval, reps = FIRST, 0
        ease = max(EASE_FLOOR, state.ease - 0.20)
    elif score == VAGUE:
        # 간격을 늘리지 않는다. 못 떠올린 것이므로 같은 자리에서 한 번 더 만난다.
        interval = max(FIRST, state.interval)
        reps = state.reps
        ease = max(EASE_FLOOR, state.ease - 0.15)
    else:
        if state.reps == 0:
            interval = FIRST
        elif state.reps == 1:
            interval = SECOND
        else:
            interval = max(SECOND, round(state.interval * state.ease))
        reps = state.reps + 1
        ease = state.ease + 0.10

    return replace(
        state,
        interval=interval, reps=reps, ease=round(ease, 2),
        due=today + timedelta(days=interval), last=today, grade=score,
    )


def is_due(state: State, today: date) -> bool:
    return state.due is not None and state.due <= today
