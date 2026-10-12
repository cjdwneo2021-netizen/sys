from datetime import datetime, timezone
import copy
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from studybot.cli import main
from studybot.config import Config
from studybot.model import Deferred, Generator
from studybot.monitoring import record_operation
from studybot.render import render
from studybot.storage import read_json, write_json, write_text


NOTE = {"markdown": "원본 설명 [SOURCE f1]", "concepts": [], "questions": []}


class Backend:
    def __init__(self, error=None):
        self.error = error

    def generate(self, prompt):
        if self.error:
            raise self.error
        return copy.deepcopy(NOTE)


class MonitoringTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.config = Config(self.root, provider="gemini", model="test", max_calls=3, daily_calls=9)

    def tearDown(self):
        self.temp.cleanup()

    def test_attempts_errors_cache_and_custom_limits_are_reported(self):
        generator = Generator(self.config, Backend())
        generator.request("first", "prompt", {"f1"})
        generator.request("first", "prompt", {"f1"})
        generator.backend = Backend(Deferred("secret must not be stored"))
        with self.assertRaises(Deferred):
            generator.request("second", "prompt", {"f1"})
        generator.finish("deferred")
        record_operation(self.config, "build", "deferred")
        render(self.root)
        usage = read_json(self.root / "state/usage.json")
        today = datetime.now(timezone.utc).date().isoformat()
        self.assertEqual(usage["days"][today], {"attempts": 2, "completed": 1, "errors": 1, "unknown": 0})
        self.assertEqual(usage["last_run"]["cache_hits"], 1)
        readme = (self.root / "README.md").read_text("utf-8")
        self.assertIn("2 / 9회", readme)
        self.assertIn("7회", readme)
        self.assertIn("재개 대기", readme)
        self.assertIn("제공업체 한도 또는 일시적 서비스 오류", readme)
        self.assertNotIn("secret", (self.root / "state/usage.json").read_text("utf-8"))

    def test_old_budget_is_preserved_across_utc_rollover(self):
        write_json(self.root / "state/budget.json", {"date": "2000-01-01", "calls": 8})
        generator = Generator(self.config, Backend())
        generator.request("first", "prompt", {"f1"})
        generator.finish("completed", 1)
        today = datetime.now(timezone.utc).date().isoformat()
        usage = read_json(self.root / "state/usage.json")
        self.assertEqual(usage["days"]["2000-01-01"]["unknown"], 8)
        self.assertEqual(usage["days"][today]["attempts"], 1)
        self.assertEqual(read_json(self.root / "state/budget.json")["calls"], 1)
        render(self.root)
        text = (self.root / "README.md").read_text("utf-8")
        self.assertIn("| 2000-01-01 | 8 | 0 | 0 | 8 |", text)
        self.assertIn("1 / 9회", text)

    def test_interrupted_attempt_and_budget_gap_remain_unknown(self):
        write_json(self.root / "state/budget.json", {"date": "2000-01-01", "calls": 8})
        write_json(self.root / "state/usage.json", {"days": {
            "2000-01-01": {"attempts": 7, "completed": 5, "errors": 1, "unknown": 0}}})
        generator = Generator(self.config, Backend())
        generator.save_usage()
        render(self.root)
        text = (self.root / "README.md").read_text("utf-8")
        self.assertIn("| 2000-01-01 | 8 | 5 | 1 | 2 |", text)
        self.assertIn("완료 미확인", text)

    def test_legacy_render_does_not_claim_live_usage_or_duplicate_sections(self):
        write_json(self.root / "state/budget.json", {"date": "2000-01-01", "calls": 8})
        write_text(self.root / "README.md", "# Course\n\nManual text\n\n## 공부 노트\n")
        render(self.root)
        first = (self.root / "README.md").read_bytes()
        render(self.root)
        self.assertEqual(first, (self.root / "README.md").read_bytes())
        text = first.decode("utf-8")
        self.assertEqual(text.count("<!-- studybot:status:start -->"), 1)
        self.assertIn("실제 실행 설정 미기록", text)
        self.assertIn("2000-01-01", text)
        self.assertIn("실시간 사용량은 아닙니다", text)
        self.assertIn("Manual text", text)
        self.assertNotIn("](state/usage.json)", text)

    def test_budget_deferral_makes_no_api_attempt_and_records_reason(self):
        today = datetime.now(timezone.utc).date().isoformat()
        write_json(self.root / "state/budget.json", {"date": today, "calls": 9})
        generator = Generator(self.config, Backend())
        with self.assertRaises(Deferred):
            generator.request("blocked", "prompt", {"f1"})
        generator.finish("deferred")
        run = read_json(self.root / "state/usage.json")["last_run"]
        self.assertEqual(run["attempts"], 0)
        self.assertEqual(run["deferred_reason"], "daily_limit")
        render(self.root)
        text = (self.root / "README.md").read_text("utf-8")
        self.assertIn("9 / 9회", text)
        self.assertIn("자체 일일 호출 한도", text)

    def test_queue_counts_import_wait_generation_and_prompt_upgrade(self):
        for lecture in ("missing", "old", "ready"):
            write_json(self.root / f"materials/{lecture}/manifest.json", {"fingerprint": "same"})
        from studybot.extract import PROMPT_VERSION
        for lecture, version in (("old", "lecture-v1"), ("ready", PROMPT_VERSION)):
            write_json(self.root / f"state/results/{lecture}.json", {
                "id": lecture, "title": lecture, "source_fingerprint": "same",
                "prompt_version": version, "note": NOTE, "sources": []})
        write_json(self.root / "state/drive.json", {"observed": {
            "new": {"fingerprint": "new"}, "ready": {"fingerprint": "changed"},
            "old": {"fingerprint": "same"}}})
        render(self.root)
        text = (self.root / "README.md").read_text("utf-8")
        self.assertIn("생성/갱신 대기 2건", text)
        self.assertIn("안정성 관찰 대기 2건", text)

    def test_cli_deferred_and_sync_failure_update_status_and_readme(self):
        argv = ["studybot", "build", "--root", str(self.root)]
        with patch("sys.argv", argv), patch("studybot.cli.generate_notes", side_effect=Deferred("quota")), \
                redirect_stdout(StringIO()):
            main()
        self.assertEqual(read_json(self.root / "state/operations.json")["build"]["status"], "deferred")
        self.assertEqual(read_json(self.root / "state/usage.json")["last_run"]["status"], "deferred")
        with patch("sys.argv", ["studybot", "sync", "--root", str(self.root)]), \
                patch.dict("os.environ", {"DRIVE_FOLDER_ID": "root"}), \
                patch("studybot.cli.Drive", return_value=object()), \
                patch("studybot.cli.synchronize", side_effect=RuntimeError("secret")), \
                redirect_stderr(StringIO()):
            with self.assertRaises(SystemExit):
                main()
        self.assertEqual(read_json(self.root / "state/operations.json")["sync"]["status"], "failed")
        self.assertIn("실패", (self.root / "README.md").read_text("utf-8"))
        self.assertNotIn("secret", (self.root / "state/operations.json").read_text("utf-8"))
