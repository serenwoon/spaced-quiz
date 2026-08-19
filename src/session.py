"""오늘 볼 것만 꺼내 주는 화면.

채점은 사람이 한다. 서술형 문항은 자동 채점이 불가능하고, 되는 척하면 학습이
망가진다. 말해보고 → 펼치고 → 스스로 누른다.

한 문항 답할 때마다 저장한다. 중간에 끊어도 푼 만큼은 남는다.
"""

from __future__ import annotations

import random
from datetime import date, timedelta
from pathlib import Path

from . import parse, progress, sr

BAR = "─" * 58


def build_queue(items, states, today, count):
    """복습할 것 먼저, 모자라면 안 본 것으로 채운다."""
    due = [i for i in items if sr.is_due(states.get(i.key, sr.State()), today)]
    fresh = [i for i in items if i.key not in states]
    random.shuffle(due)
    random.shuffle(fresh)
    return (due + fresh)[:count], len(due), len(fresh)


def streak(states, today):
    days = {s.last for s in states.values() if s.last}
    if not days:
        return 0
    n, cur = 0, today
    if cur not in days:
        cur -= timedelta(days=1)
        if cur not in days:
            return 0
    while cur in days:
        n += 1
        cur -= timedelta(days=1)
    return n


def stats(items, states, skipped, today, out=print, mismatched=()):
    due = sum(1 for i in items if sr.is_due(states.get(i.key, sr.State()), today))
    seen = sum(1 for i in items if i.key in states)
    out(f"긁힌 문항  {len(items)}개")
    out(f"푼 적 있음 {seen}개 · 오늘 볼 것 {due}개 · 아직 안 본 것 {len(items) - seen}개")
    out(f"연속       {streak(states, today)}일")
    nxt = sorted(s.due for s in states.values() if s.due and s.due > today)
    if nxt:
        out(f"다음 예정  {nxt[0]} ({(nxt[0] - today).days}일 뒤)")
    for s in skipped:
        out(f"  ⓘ 건너뛴 파일: {s} (문항이 안 긁혔다)")
    for name, declared, got in mismatched:
        out(f"  ⚠️ {name}: 머리말은 {declared}문항이라는데 {got}개만 긁혔다")


def run(quiz_dir: Path, ledger: Path, count: int, today: date | None = None) -> None:
    today = today or date.today()
    items, skipped, mismatched = parse.load(quiz_dir)
    states = progress.load(ledger)

    queue, n_due, _ = build_queue(items, states, today, count)
    if not queue:
        print("오늘 볼 것이 없습니다.")
        stats(items, states, skipped, today, mismatched=mismatched)
        return

    print(f"\n오늘 {len(queue)}문항 (복습 {min(n_due, len(queue))} · 새것 {max(0, len(queue) - n_due)})")
    print(f"연속 {streak(states, today)}일 · 긁힌 문항 {len(items)}개")
    if skipped:
        print(f"ⓘ 문항이 안 긁혀 뺀 파일: {', '.join(skipped)}")
    for name, declared, got in mismatched:
        print(f"⚠️ {name}: 머리말은 {declared}문항이라는데 {got}개만 긁혔다")

    tally = {sr.WRONG: 0, sr.VAGUE: 0, sr.RIGHT: 0}
    for n, item in enumerate(queue, 1):
        print(f"\n{BAR}\n[{n}/{len(queue)}]  {item.label}  {item.mark}\n")
        print(item.question)
        try:
            input("\n  Enter 답 보기 ")
        except (EOFError, KeyboardInterrupt):
            print("\n그만둡니다. 여기까지는 저장됐습니다.")
            break
        print(f"\n{BAR}")
        print(item.answer)
        if item.source:
            print(f"\n  📎 {item.source}")

        score = None
        while score is None:
            try:
                raw = input("\n  [1] 틀림  [2] 애매  [3] 맞음  > ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n그만둡니다. 여기까지는 저장됐습니다.")
                return
            if raw in ("1", "2", "3"):
                score = int(raw)

        states[item.key] = sr.grade(states.get(item.key, sr.State()), score, today)
        tally[score] += 1
        progress.save(states, ledger, today)   # 한 문항마다 저장한다
        nxt = states[item.key]
        print(f"  → {sr.LABEL[score]} · 다음 {nxt.due} ({nxt.interval}일 뒤)")

    print(f"\n{BAR}")
    done = sum(tally.values())
    if done:
        print(f"오늘 {done}문항 — 맞음 {tally[sr.RIGHT]} · 애매 {tally[sr.VAGUE]} · 틀림 {tally[sr.WRONG]}")
        print(f"연속 {streak(states, today)}일")
    print(f"진도: {ledger}")
