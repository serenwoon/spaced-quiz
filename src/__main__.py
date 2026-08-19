"""python -m src

경로를 매번 치지 않도록 `.quizrc` 를 읽는다. 자세한 것은 `config.py`.
아무 폴더에서나 한 단어로 부르려면 저장소 폴더를 PATH 에 넣고 `quiz` 를 쓴다.
"""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

from . import cli, config, parse, progress, session


def main() -> None:
    cli.utf8_output()
    ap = argparse.ArgumentParser(
        prog="quiz",
        description="마크다운 노트의 문항을 간격 반복으로 푼다",
        epilog="경로를 매번 치기 싫으면 .quizrc 를 만든다 (.quizrc.example 참고)",
    )
    ap.add_argument("--dir", help="퀴즈 노트 폴더")
    ap.add_argument("--ledger", help="진도 파일 (기본 <dir>/_progress.md)")
    ap.add_argument("--count", type=int, help="오늘 볼 문항 수 (기본 10)")
    ap.add_argument("--stats", action="store_true", help="풀지 않고 현황만")
    ap.add_argument("--where", action="store_true", help="어느 설정을 읽었는지 보여준다")
    args = ap.parse_args()

    cfg, cfg_path = config.load()
    got = config.resolve(args, cfg)

    quiz_dir = Path(got["dir"])
    ledger = Path(got["ledger"]) if got["ledger"] else quiz_dir / "_progress.md"

    if args.where:
        print(f"설정 파일 : {cfg_path or '없음 (.quizrc 를 만들면 경로를 안 쳐도 된다)'}")
        print(f"노트 폴더 : {quiz_dir}  {'✓' if quiz_dir.is_dir() else '✗ 없다'}")
        print(f"진도 파일 : {ledger}  {'✓' if ledger.is_file() else '(아직 없음)'}")
        print(f"문항 수   : {got['count']}")
        return

    for key in cfg.get("_unknown", []):
        print(f"  ⚠️ {cfg_path}: 모르는 설정 「{key}」 — 무시했다")
    if "_bad_count" in got:
        print(f"  ⚠️ count 값 「{got['_bad_count']}」을 못 읽어 10으로 간다")

    if not quiz_dir.is_dir():
        raise SystemExit(
            f"폴더가 없다: {quiz_dir}\n"
            f"  --dir 로 주거나 .quizrc 에 적어라 (.quizrc.example 참고)"
        )

    if args.stats:
        items, skipped, mismatched = parse.load(quiz_dir)
        session.stats(items, progress.load(ledger), skipped, date.today(),
                      mismatched=mismatched)
        return
    session.run(quiz_dir, ledger, got["count"])


if __name__ == "__main__":
    main()
