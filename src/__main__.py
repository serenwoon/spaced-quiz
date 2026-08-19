"""python -m src --dir <노트 폴더>"""

from __future__ import annotations

import argparse
import os
from datetime import date
from pathlib import Path

from . import cli, parse, progress, session


def main() -> None:
    cli.utf8_output()
    ap = argparse.ArgumentParser(prog="spaced-quiz", description="마크다운 노트의 문항을 간격 반복으로 푼다")
    ap.add_argument("--dir", default=os.environ.get("QUIZ_DIR", "quiz"),
                    help="퀴즈 노트 폴더 (기본 ./quiz, 환경변수 QUIZ_DIR)")
    ap.add_argument("--ledger", default=os.environ.get("QUIZ_LEDGER"),
                    help="진도 파일 (기본 <dir>/_progress.md)")
    ap.add_argument("--count", type=int, default=10, help="오늘 볼 문항 수 (기본 10)")
    ap.add_argument("--stats", action="store_true", help="풀지 않고 현황만")
    args = ap.parse_args()

    quiz_dir = Path(args.dir)
    if not quiz_dir.is_dir():
        raise SystemExit(f"폴더가 없다: {quiz_dir}")
    ledger = Path(args.ledger) if args.ledger else quiz_dir / "_progress.md"

    if args.stats:
        items, skipped, mismatched = parse.load(quiz_dir)
        session.stats(items, progress.load(ledger), skipped, date.today(), mismatched=mismatched)
        return
    session.run(quiz_dir, ledger, args.count)


if __name__ == "__main__":
    main()
