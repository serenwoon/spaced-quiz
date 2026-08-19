"""설정 파일 — 매일 치는 글자 수를 줄인다.

경로를 인자로 받게 만들었더니 실행 명령이 167자가 됐다. 그 길이를 매일 치는
도구는 안 쓰인다. 이 저장소가 대신하려는 옵시디언 플러그인이 정확히 그렇게
죽었다 — 설정까지 다 돼 있는데 22일 동안 한 번도 안 돌았다.

기능이 모자라서가 아니라 **부르기 번거로워서** 죽는다.

형식은 `키 = 값` 한 줄씩이다. TOML이나 JSON을 쓰지 않은 이유는 파이썬 3.10에
`tomllib`이 없고, 설정 넉 줄을 읽자고 의존성을 받거나 파서를 짜는 것이 이
저장소가 하려는 일과 반대이기 때문이다.

우선순위는 **명령줄 인자 > 환경변수 > 설정 파일 > 기본값**이다. 설정은
기본값을 바꾸는 것이지 인자를 이기지 않는다.

찾는 자리는 셋이다.

    QUIZ_CONFIG 가 가리키는 파일
    ./.quizrc          (지금 폴더)
    ~/.quizrc          (홈)

🔴 `.quizrc` 는 저장소에 안 넣는다. 내 노트 폴더의 절대경로가 들어가기 때문이다.
대신 `.quizrc.example` 을 두고 `.gitignore` 에 실물을 적어둔다. 점검 도구는
공개하고 점검 대상 경로는 공개하지 않는다.
"""

from __future__ import annotations

import os
from pathlib import Path

NAME = ".quizrc"
KEYS = ("dir", "ledger", "count")


def find(start: Path | None = None) -> Path | None:
    """설정 파일 자리. 없으면 None."""
    env = os.environ.get("QUIZ_CONFIG")
    if env:
        p = Path(env)
        return p if p.is_file() else None
    for base in (start or Path.cwd(), Path.home()):
        p = Path(base) / NAME
        if p.is_file():
            return p
    return None


def parse(text: str) -> dict:
    """`키 = 값` 한 줄씩. `#` 뒤는 주석이고 모르는 키는 조용히 버리지 않는다."""
    out, unknown = {}, []
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        if "=" not in line:
            unknown.append(line)
            continue
        key, value = (s.strip() for s in line.split("=", 1))
        value = value.strip('"').strip("'")
        if key in KEYS:
            out[key] = value
        else:
            unknown.append(key)
    if unknown:
        out["_unknown"] = unknown
    return out


def load(start: Path | None = None) -> tuple:
    """(설정, 읽은 파일). 파일이 없으면 ({}, None)."""
    path = find(start)
    if path is None:
        return {}, None
    return parse(path.read_text(encoding="utf-8")), path


def resolve(args, cfg: dict) -> dict:
    """명령줄 인자 > 환경변수 > 설정 파일 > 기본값.

    `count` 는 argparse 가 기본값 10을 이미 채워 넣으므로, 사용자가 실제로
    준 것인지 기본값인지 가릴 수 없다. 그래서 `None` 을 기본값으로 두고
    여기서 판단한다.
    """
    got = {}
    got["dir"] = args.dir or os.environ.get("QUIZ_DIR") or cfg.get("dir") or "quiz"
    got["ledger"] = args.ledger or os.environ.get("QUIZ_LEDGER") or cfg.get("ledger") or ""
    count = args.count if args.count is not None else cfg.get("count")
    try:
        got["count"] = int(count) if count is not None else 10
    except (TypeError, ValueError):
        got["count"] = 10
        got["_bad_count"] = str(count)
    return got
