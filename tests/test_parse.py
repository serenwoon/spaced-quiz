"""파싱 — 형식이 어긋나는 자리를 붙든다."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import parse  # noqa: E402

SAMPLE = Path(__file__).resolve().parent.parent / "fixtures" / "sample"


class TestSample(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.items, cls.skipped, cls.mismatched = parse.load(SAMPLE)

    def test_예시에서_여섯_문항이_나온다(self):
        self.assertEqual(len(self.items), 6)

    def test_문항이_없는_파일은_건너뛴_것으로_밝힌다(self):
        """조용히 사라지는 것이 제일 나쁘다."""
        self.assertEqual(self.skipped, ["99_읽을거리"])

    def test_헤딩_뒤에_글자가_붙어도_긁힌다(self):
        """### Q3 🔴 **최종** 처럼 꼬리표가 붙는 일이 흔하다."""
        self.assertIn("01#Q3", [i.key for i in self.items])
        self.assertIn("02#Q2", [i.key for i in self.items])

    def test_파트는_문항이_열릴_때의_것이다(self):
        """닫을 때 읽으면 각 파트의 마지막 문항이 다음 파트 이름을 단다."""
        part = {i.key: i.part for i in self.items}
        self.assertEqual(part["01#Q1"], "A")
        self.assertEqual(part["01#Q2"], "A")
        self.assertEqual(part["01#Q3"], "B")

    def test_난이도_표시를_그대로_들고_있는다(self):
        mark = {i.key: i.mark for i in self.items}
        self.assertEqual(mark["01#Q1"], "🟢")
        self.assertEqual(mark["02#Q2"], "🔴🔴")

    def test_출처를_답에서_떼어낸다(self):
        item = next(i for i in self.items if i.key == "01#Q1")
        self.assertEqual(item.source, "추출의 변수")
        self.assertNotIn("📎", item.answer)

    def test_출처가_없어도_된다(self):
        self.assertEqual(next(i for i in self.items if i.key == "01#Q2").source, "")

    def test_답에_든_표가_살아_있는다(self):
        item = next(i for i in self.items if i.key == "01#Q2")
        self.assertIn("| 과다추출 |", item.answer)

    def test_키가_안_겹친다(self):
        keys = [i.key for i in self.items]
        self.assertEqual(len(keys), len(set(keys)))


class TestQuirks(unittest.TestCase):
    def test_콜아웃_이름을_안_본다(self):
        """답이든 Answer든 상관없이 받는다."""
        text = "### Q1\n질문\n\n> [!success]- Answer\n> 답\n"
        self.assertEqual(len(parse.parse_text(text, "01_x")), 1)

    def test_답이_없는_문항은_버린다(self):
        text = "### Q1\n물어보기만 하고 답이 없다\n"
        self.assertEqual(parse.parse_text(text, "01_x"), [])

    def test_번호_앞머리가_없으면_파일명을_쓴다(self):
        text = "### Q1\n질문\n\n> [!success]- 답\n> 답\n"
        self.assertEqual(parse.parse_text(text, "메모")[0].key, "메모#Q1")

    def test_빈_문서는_빈_목록이다(self):
        self.assertEqual(parse.parse_text("", "01_x"), [])


class TestCountMismatch(unittest.TestCase):
    """절반만 긁히는 파일이 제일 위험하다.

    아예 안 긁히면 「건너뜀」으로 드러나는데, 일부만 긁히면 그 파일이 도는
    것처럼 보이면서 나머지가 조용히 사라진다.
    """

    def setUp(self):
        _, _, self.mismatched = parse.load(SAMPLE)

    def test_머리말_수와_긁힌_수가_다르면_알린다(self):
        names = {m[0] for m in self.mismatched}
        self.assertIn("03_커피 — 절반만 긁히는 파일", names)

    def test_양쪽_수를_다_들고_있는다(self):
        """어느 쪽이 맞는지는 정하지 않는다. 안 맞는다는 것만 말한다."""
        row = next(m for m in self.mismatched if m[0].startswith("03_"))
        self.assertEqual((row[1], row[2]), (4, 1))

    def test_수가_맞는_파일은_안_알린다(self):
        names = {m[0] for m in self.mismatched}
        self.assertNotIn("01_커피 — 추출의 기본", names)
        self.assertNotIn("02_커피 — 로스팅", names)
