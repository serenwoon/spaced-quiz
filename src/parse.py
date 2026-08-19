"""마크다운 노트에서 문항을 긁는다.

기대하는 모양은 이렇다.

    ### Q1 🟡
    질문 본문. 여러 줄이어도 된다.

    > [!success]- 답
    > 답 본문.
    > 📎 [[출처 노트]]

헤딩 뒤에 무엇이 붙든 받는다. 난이도 표시를 달거나 `**최종**` 같은 꼬리표를
붙이는 일이 흔해서, 거기서 엄격하면 파일마다 마지막 문항 하나씩을 조용히
놓친다. 실제로 그렇게 놓쳤다.

접힘 콜아웃의 이름은 안 본다. `[!success]-` 뒤가 「답」이든 「Answer」든 상관없다.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

_Q = re.compile(r"^###\s+Q(\d+)\b(.*)$")
_ANS = re.compile(r"^>\s*\[!success\]-")
_PART = re.compile(r"^##\s+([A-Z])\.\s*(.+?)\s*$")
_SRC = re.compile(r"📎\s*\[\[([^\]\|]+)")
_PREFIX = re.compile(r"^([0-9]+(?:-[0-9]+)?)[_\s]")
_COUNT = re.compile(r"^count:\s*(\d+)\s*$", re.M)
_MARK = re.compile(r"[🟢🟡🔴]+")


@dataclass(frozen=True)
class Item:
    key: str          # 61-1#Q7 — 진도 파일의 열쇠
    file: str
    number: int
    mark: str
    part: str
    question: str
    answer: str
    source: str

    @property
    def label(self) -> str:
        return f"{self.key.split('#')[0]} · Q{self.number}"


def _flush(buf: list) -> str:
    while buf and not buf[-1].strip():
        buf.pop()
    return "\n".join(buf).strip()


def parse_text(text: str, stem: str) -> list:
    """한 파일의 문항들. 답이 없는 문항은 버린다 — 물어볼 수는 있어도 대조를 못 한다."""
    prefix = (_PREFIX.match(stem) or [None, stem])[1]
    items, part = [], ""
    n = mark = q_part = None
    qbuf: list = []
    abuf: list = []
    in_answer = False

    def close():
        nonlocal n, mark, q_part, qbuf, abuf, in_answer
        if n is not None and abuf:
            ans = _flush(abuf)
            src = _SRC.search(ans)
            items.append(Item(
                key=f"{prefix}#Q{n}", file=stem, number=n,
                mark=mark or "", part=q_part or "",
                question=_flush(qbuf),
                answer=re.sub(r"\n?📎.*$", "", ans, flags=re.S).strip(),
                source=src.group(1).strip() if src else "",
            ))
        n = mark = q_part = None
        qbuf, abuf, in_answer = [], [], False

    for line in text.splitlines():
        mp = _PART.match(line)
        if mp:
            part = mp.group(1)
            continue
        mq = _Q.match(line)
        if mq:
            close()
            n = int(mq.group(1))
            # 🔴 파트는 문항이 열릴 때 붙잡는다. 닫을 때 읽으면 이미 다음 절
            # 헤딩을 지난 뒤라, 각 파트의 마지막 문항이 다음 파트 이름을 단다.
            q_part = part
            found = _MARK.search(mq.group(2))
            mark = found.group(0) if found else ""
            continue
        if n is None:
            continue
        if _ANS.match(line):
            in_answer = True
            continue
        if in_answer:
            if line.startswith(">"):
                abuf.append(re.sub(r"^>\s?", "", line))
            elif line.strip():
                close()
        else:
            qbuf.append(line)
    close()
    return items


def load(quiz_dir: Path) -> tuple:
    """(문항, 건너뛴 파일, 수가 안 맞는 파일).

    건너뛸 파일 목록을 손으로 적지 않는다. 문항이 하나도 안 긁힌 파일을 건너뛴
    것으로 돌려주면 목록이 필요 없고, 목록 밖의 파일이 조용히 사라지는 일도
    없다.

    🔴 **더 위험한 건 절반만 긁히는 파일이다.** 아예 안 긁히면 건너뛴 것으로
    드러나는데, 일부만 긁히면 그 파일이 도는 것처럼 보이면서 나머지가 조용히
    사라진다. 그래서 머리말에 `count:`가 적혀 있으면 긁힌 수와 대조하고 안 맞는
    것을 따로 돌려준다. 어느 쪽이 맞는지는 정하지 않는다 — 안 맞는다는 것만
    말한다.
    """
    items, skipped, mismatched = [], [], []
    for p in sorted(Path(quiz_dir).glob("*.md")):
        text = p.read_text(encoding="utf-8")
        got = parse_text(text, p.stem)
        if not got:
            skipped.append(p.stem)
            continue
        items.extend(got)
        declared = _COUNT.search(text)
        if declared and int(declared.group(1)) != len(got):
            mismatched.append((p.stem, int(declared.group(1)), len(got)))
    return items, skipped, mismatched
