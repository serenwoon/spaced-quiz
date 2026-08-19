"""간격 계산."""

from __future__ import annotations

import sys
import unittest
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import sr  # noqa: E402

TODAY = date(2026, 8, 19)


class TestSchedule(unittest.TestCase):
    def 맞음(self, n, s=None):
        s = s or sr.State()
        for _ in range(n):
            s = sr.grade(s, sr.RIGHT, TODAY)
        return s

    def test_처음_맞히면_내일_다시_본다(self):
        s = self.맞음(1)
        self.assertEqual((s.interval, s.reps), (1, 1))
        self.assertEqual(s.due, TODAY + timedelta(days=1))

    def test_두_번째는_엿새_뒤다(self):
        self.assertEqual(self.맞음(2).interval, 6)

    def test_세_번째부터_ease_를_곱한다(self):
        self.assertGreater(self.맞음(3).interval, 6)

    def test_맞힐수록_간격이_는다(self):
        prev = 0
        for n in range(1, 6):
            cur = self.맞음(n).interval
            self.assertGreaterEqual(cur, prev)
            prev = cur

    def test_애매는_간격을_안_늘린다(self):
        """「아 그렇구나」는 못 떠올린 것이다. 늘리면 다음엔 더 안 떠오른다."""
        s = self.맞음(3)
        self.assertEqual(sr.grade(s, sr.VAGUE, TODAY).interval, s.interval)

    def test_애매는_ease_를_깎는다(self):
        s = self.맞음(1)
        self.assertLess(sr.grade(s, sr.VAGUE, TODAY).ease, s.ease)

    def test_애매는_연속을_안_깎는다(self):
        s = self.맞음(3)
        self.assertEqual(sr.grade(s, sr.VAGUE, TODAY).reps, s.reps)

    def test_틀리면_처음으로_돌아간다(self):
        s = sr.grade(self.맞음(4), sr.WRONG, TODAY)
        self.assertEqual((s.interval, s.reps), (1, 0))

    def test_ease_는_바닥_아래로_안_내려간다(self):
        s = sr.State()
        for _ in range(40):
            s = sr.grade(s, sr.WRONG, TODAY)
        self.assertGreaterEqual(s.ease, sr.EASE_FLOOR)

    def test_안_본_문항은_due_가_아니다(self):
        self.assertFalse(sr.is_due(sr.State(), TODAY))
        self.assertFalse(sr.State().seen)

    def test_기한이_지나야_due_다(self):
        s = self.맞음(1)
        self.assertFalse(sr.is_due(s, TODAY))
        self.assertTrue(sr.is_due(s, TODAY + timedelta(days=1)))
        self.assertTrue(sr.is_due(s, TODAY + timedelta(days=9)))

    def test_상태는_제자리에서_안_바뀐다(self):
        """채점은 새 상태를 만든다."""
        s = sr.State()
        sr.grade(s, sr.RIGHT, TODAY)
        self.assertEqual(s.interval, 0)
