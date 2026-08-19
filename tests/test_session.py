"""오늘의 큐와 연속일수."""

from __future__ import annotations

import sys
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import parse, progress, session, sr  # noqa: E402

TODAY = date(2026, 8, 19)
SAMPLE = Path(__file__).resolve().parent.parent / "fixtures" / "sample"


def state(days_ago: int, due_in: int):
    return sr.State(interval=1, reps=1, ease=2.5,
                    due=TODAY + timedelta(days=due_in),
                    last=TODAY - timedelta(days=days_ago), grade=3)


class TestQueue(unittest.TestCase):
    def setUp(self):
        self.items, *_ = parse.load(SAMPLE)

    def test_복습할_것이_새것보다_먼저_나온다(self):
        target = self.items[3].key
        q, n_due, _ = session.build_queue(self.items, {target: state(1, 0)}, TODAY, 5)
        self.assertEqual(n_due, 1)
        self.assertEqual(q[0].key, target)

    def test_요청한_수만큼만_준다(self):
        q, _, _ = session.build_queue(self.items, {}, TODAY, 2)
        self.assertEqual(len(q), 2)

    def test_문항보다_많이_요청해도_있는_만큼만(self):
        q, _, _ = session.build_queue(self.items, {}, TODAY, 999)
        self.assertEqual(len(q), len(self.items))

    def test_아직_때가_아닌_것은_안_나온다(self):
        states = {i.key: state(1, 5) for i in self.items}
        q, n_due, _ = session.build_queue(self.items, states, TODAY, 5)
        self.assertEqual((len(q), n_due), (0, 0))


class TestStreak(unittest.TestCase):
    def test_오늘_풀었으면_오늘부터_센다(self):
        self.assertEqual(session.streak({"a": state(0, 1), "b": state(1, 1)}, TODAY), 2)

    def test_오늘_안_풀었으면_어제부터_센다(self):
        self.assertEqual(session.streak({"a": state(1, 1), "b": state(2, 1)}, TODAY), 2)

    def test_사흘_비면_끊긴다(self):
        self.assertEqual(session.streak({"a": state(3, 1)}, TODAY), 0)

    def test_진도가_없으면_0일(self):
        self.assertEqual(session.streak({}, TODAY), 0)


class TestLedgerPath(unittest.TestCase):
    def test_진도는_넘겨준_경로에만_쓴다(self):
        """기본값을 모듈 상수에 묶으면 시험이 임시 경로를 가리켜도 진짜 파일에
        쓴다. 실제로 그 사고가 났고, 이 시험이 그 자리를 붙든다."""
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            mine, other = Path(a) / "_progress.md", Path(b) / "_progress.md"
            progress.save({"01#Q1": sr.grade(sr.State(), sr.RIGHT, TODAY)}, mine, TODAY)
            self.assertTrue(mine.exists())
            self.assertFalse(other.exists())


class TestStats(unittest.TestCase):
    def test_건너뛴_파일을_화면에_밝힌다(self):
        items, skipped, _ = parse.load(SAMPLE)
        lines = []
        session.stats(items, {}, skipped, TODAY, out=lines.append)
        self.assertTrue(any("건너뛴 파일" in l for l in lines))
        self.assertTrue(any("99_읽을거리" in l for l in lines))

    def test_긁힌_문항_수를_밝힌다(self):
        items, skipped, _ = parse.load(SAMPLE)
        lines = []
        session.stats(items, {}, skipped, TODAY, out=lines.append)
        self.assertTrue(any(f"{len(items)}개" in l for l in lines))
