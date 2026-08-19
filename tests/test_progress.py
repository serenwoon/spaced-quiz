"""진도 — 왕복에서 안 상하는가."""

from __future__ import annotations

import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import progress, sr  # noqa: E402

TODAY = date(2026, 8, 19)


class TestRoundTrip(unittest.TestCase):
    def 왕복(self, states):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "_progress.md"
            progress.save(states, p, TODAY)
            return progress.load(p), p.read_bytes()

    def test_저장하고_읽으면_그대로다(self):
        states = {
            "61-1#Q1": sr.grade(sr.State(), sr.RIGHT, TODAY),
            "16-2#Q30": sr.grade(sr.State(), sr.WRONG, TODAY),
            "69-3#Q7": sr.grade(sr.grade(sr.State(), sr.RIGHT, TODAY), sr.VAGUE, TODAY),
        }
        self.assertEqual(self.왕복(states)[0], states)

    def test_빈_진도도_왕복한다(self):
        self.assertEqual(self.왕복({})[0], {})

    def test_없는_파일은_빈_진도다(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(progress.load(Path(tmp) / "없음.md"), {})

    def test_줄바꿈이_LF다(self):
        _, raw = self.왕복({"61-1#Q1": sr.grade(sr.State(), sr.RIGHT, TODAY)})
        self.assertEqual(raw.count(b"\r"), 0)

    def test_폴더가_없으면_만든다(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "없던폴더" / "_progress.md"
            progress.save({}, p, TODAY)
            self.assertTrue(p.exists())

    def test_키_순으로_정렬한다(self):
        """정렬돼 있어야 두 기기가 다른 문항을 풀었을 때 git이 알아서 합친다."""
        keys = ["69-3#Q2", "16-1#Q10", "16-1#Q2", "61-1#Q1"]
        states = {k: sr.grade(sr.State(), sr.RIGHT, TODAY) for k in keys}
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "_progress.md"
            progress.save(states, p, TODAY)
            order = [l.split("|")[1].strip()
                     for l in p.read_text(encoding="utf-8").splitlines()
                     if l.startswith("| ") and "#Q" in l]
        self.assertEqual(order, ["16-1#Q2", "16-1#Q10", "61-1#Q1", "69-3#Q2"])

    def test_Q10_이_Q2_뒤에_온다(self):
        """문자열 정렬이면 Q10이 Q2 앞에 온다."""
        self.assertLess(progress.sortkey("16-1#Q2"), progress.sortkey("16-1#Q10"))

    def test_모양이_다른_줄은_무시한다(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "_progress.md"
            p.write_text("| 키 | 다음 |\n|---|---|\n| 이건 | 표가 아님 |\n", encoding="utf-8")
            self.assertEqual(progress.load(p), {})

    def test_경로를_문자열로_줘도_된다(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = str(Path(tmp) / "_progress.md")
            progress.save({"01#Q1": sr.grade(sr.State(), sr.RIGHT, TODAY)}, p, TODAY)
            self.assertEqual(list(progress.load(p)), ["01#Q1"])
