"""진도 — 마크다운 표 하나.

간격 반복 도구는 보통 진도를 자기 데이터베이스에 넣는데, 그러면 기기를 옮길 때
따라오지 않는다. 옵시디언 간격반복 플러그인이 그렇다. 진도가
`.obsidian/plugins/…/data.json`에 있고 그 파일은 보통 `.gitignore` 대상이라,
한쪽에서 복습해도 다른 쪽은 모른다.

그래서 여기서는 진도를 **노트 폴더 안 마크다운**에 둔다. 노트를 git으로 옮기는
사람이면 진도도 같이 따라간다.

파일이 하나이고 키 순으로 정렬돼 있는 것이 중요하다. 양쪽에서 서로 다른 문항을
풀면 git이 알아서 합치고, 같은 문항을 같은 날 양쪽에서 풀었을 때만 충돌이 난다.
"""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path

from .sr import State

HEAD = """---
title: 퀴즈 진도
type: reference
updated: {today}
---

> 간격 반복 퀴즈가 읽고 쓰는 파일이다. 손으로 고쳐도 되지만 표 모양은 지킬 것.
> 문항 키는 `파일앞번호#Q번호`다. 파일 이름의 앞번호를 바꾸면 그 파일 진도가 끊긴다.

| 키 | 다음 | 간격 | 연속 | ease | 마지막 | 결과 |
|---|---|---|---|---|---|---|
"""

_ROW = re.compile(
    r"^\|\s*([^|]+?)\s*\|\s*([\d-]+)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|"
    r"\s*([\d.]+)\s*\|\s*([\d-]+)\s*\|\s*(\S+)\s*\|$"
)
GRADE = {"틀림": 1, "애매": 2, "맞음": 3}
LABEL = {v: k for k, v in GRADE.items()}


def load(path: Path) -> dict:
    path = Path(path)
    if not path.exists():
        return {}
    out = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        m = _ROW.match(line)
        if not m:
            continue
        key, due, interval, reps, ease, last, label = m.groups()
        out[key] = State(
            interval=int(interval), reps=int(reps), ease=float(ease),
            due=date.fromisoformat(due), last=date.fromisoformat(last),
            grade=GRADE.get(label, 0),
        )
    return out


def save(states: dict, path: Path, today: date | None = None) -> None:
    today = today or date.today()
    path = Path(path)
    rows = [
        f"| {k} | {s.due} | {s.interval} | {s.reps} | {s.ease:.2f} | {s.last} | {LABEL.get(s.grade, '?')} |"
        for k, s in sorted(states.items(), key=lambda kv: sortkey(kv[0]))
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(HEAD.format(today=today) + "\n".join(rows) + "\n",
                    encoding="utf-8", newline="\n")


def sortkey(key: str):
    """61-1#Q7 을 (61, 1, 7) 로. 문자열 정렬이면 Q10이 Q2 앞에 온다."""
    m = re.match(r"(\d+)(?:-(\d+))?#Q(\d+)$", key)
    if not m:
        return (9999, 9999, 9999, key)
    a, b, q = m.groups()
    return (int(a), int(b or 0), int(q), "")
