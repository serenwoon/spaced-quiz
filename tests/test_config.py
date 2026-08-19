"""설정 파일과 우선순위."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import config  # noqa: E402


class Args:
    def __init__(self, dir=None, ledger=None, count=None):
        self.dir, self.ledger, self.count = dir, ledger, count


class TestParse(unittest.TestCase):
    def test_키_값을_읽는다(self):
        got = config.parse("dir = /notes\ncount = 5\n")
        self.assertEqual(got["dir"], "/notes")
        self.assertEqual(got["count"], "5")

    def test_주석과_빈_줄을_건너뛴다(self):
        got = config.parse("# 주석\n\ndir = /notes   # 뒤 주석\n")
        self.assertEqual(got["dir"], "/notes")

    def test_따옴표를_벗긴다(self):
        self.assertEqual(config.parse('dir = "/한글 폴더"\n')["dir"], "/한글 폴더")

    def test_경로에_든_등호는_안_자른다(self):
        """값 쪽의 = 는 값의 일부다. split(1) 이 아니면 경로가 잘린다."""
        self.assertEqual(config.parse("dir = /a=b/c\n")["dir"], "/a=b/c")

    def test_모르는_키를_조용히_버리지_않는다(self):
        got = config.parse("dir = /notes\ncolour = red\n")
        self.assertIn("colour", got["_unknown"])

    def test_등호가_없는_줄도_알린다(self):
        self.assertIn("이건 뭐지", config.parse("이건 뭐지\n")["_unknown"])

    def test_빈_파일은_빈_설정이다(self):
        self.assertEqual(config.parse(""), {})


class TestPrecedence(unittest.TestCase):
    def setUp(self):
        self.saved = {k: os.environ.pop(k, None) for k in ("QUIZ_DIR", "QUIZ_LEDGER")}

    def tearDown(self):
        for k, v in self.saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    def test_인자가_설정을_이긴다(self):
        got = config.resolve(Args(dir="/from-arg"), {"dir": "/from-file"})
        self.assertEqual(got["dir"], "/from-arg")

    def test_환경변수가_설정을_이긴다(self):
        os.environ["QUIZ_DIR"] = "/from-env"
        self.assertEqual(config.resolve(Args(), {"dir": "/from-file"})["dir"], "/from-env")

    def test_인자가_환경변수를_이긴다(self):
        os.environ["QUIZ_DIR"] = "/from-env"
        self.assertEqual(config.resolve(Args(dir="/from-arg"), {})["dir"], "/from-arg")

    def test_아무것도_없으면_기본값이다(self):
        got = config.resolve(Args(), {})
        self.assertEqual((got["dir"], got["count"]), ("quiz", 10))

    def test_설정의_count_를_숫자로_읽는다(self):
        self.assertEqual(config.resolve(Args(), {"count": "5"})["count"], 5)

    def test_count_0_도_인자가_이긴다(self):
        """argparse 기본값을 10으로 두면 사용자가 준 것인지 못 가린다.
        None 을 기본값으로 두는 이유다."""
        self.assertEqual(config.resolve(Args(count=0), {"count": "5"})["count"], 0)

    def test_숫자가_아닌_count_는_기본값으로_가되_알린다(self):
        got = config.resolve(Args(), {"count": "다섯"})
        self.assertEqual(got["count"], 10)
        self.assertEqual(got["_bad_count"], "다섯")


class TestFind(unittest.TestCase):
    def setUp(self):
        self.saved = os.environ.pop("QUIZ_CONFIG", None)

    def tearDown(self):
        if self.saved is None:
            os.environ.pop("QUIZ_CONFIG", None)
        else:
            os.environ["QUIZ_CONFIG"] = self.saved

    def test_지금_폴더의_quizrc_를_찾는다(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / config.NAME
            p.write_text("dir = /notes\n", encoding="utf-8")
            self.assertEqual(config.find(Path(tmp)), p)

    def test_환경변수가_가리키는_파일이_먼저다(self):
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            here = Path(a) / config.NAME
            here.write_text("dir = /here\n", encoding="utf-8")
            there = Path(b) / "custom.rc"
            there.write_text("dir = /there\n", encoding="utf-8")
            os.environ["QUIZ_CONFIG"] = str(there)
            self.assertEqual(config.find(Path(a)), there)

    def test_환경변수가_없는_파일을_가리키면_None(self):
        os.environ["QUIZ_CONFIG"] = "/없는/파일.rc"
        self.assertIsNone(config.find())

    def test_설정이_없으면_빈_설정이다(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg, path = config.load(Path(tmp))
            self.assertEqual(cfg, {})
            # 홈에 .quizrc 가 있으면 그걸 잡으므로 path 는 단정하지 않는다


class TestExampleShipped(unittest.TestCase):
    def test_예시_설정이_저장소에_있다(self):
        p = Path(__file__).resolve().parent.parent / ".quizrc.example"
        self.assertTrue(p.exists())

    def test_예시가_실제로_읽힌다(self):
        p = Path(__file__).resolve().parent.parent / ".quizrc.example"
        got = config.parse(p.read_text(encoding="utf-8"))
        self.assertNotIn("_unknown", got)
        self.assertIn("dir", got)

    def test_실물_설정은_저장소에_없다(self):
        """경로가 든 .quizrc 는 .gitignore 대상이다."""
        root = Path(__file__).resolve().parent.parent
        ignore = (root / ".gitignore").read_text(encoding="utf-8")
        self.assertIn(".quizrc", ignore)


class TestLauncher(unittest.TestCase):
    def test_배치_파일이_ASCII_뿐이다(self):
        """cmd.exe 는 .cmd 를 OEM 코드페이지로 읽는다. UTF-8 한글 주석을 넣으면
        깨져서 엉뚱한 명령으로 실행된다. 실제로 그랬다."""
        p = Path(__file__).resolve().parent.parent / "quiz.cmd"
        self.assertEqual(sum(1 for b in p.read_bytes() if b > 127), 0)

    def test_실행기_둘이_다_있다(self):
        root = Path(__file__).resolve().parent.parent
        self.assertTrue((root / "quiz.cmd").exists())   # 윈도우
        self.assertTrue((root / "quiz").exists())        # 맥·리눅스
