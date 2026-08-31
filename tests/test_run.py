#!/usr/bin/env python3
"""Deterministic tests for the model runner's scoring and case discovery."""

import importlib.util
import json
import re
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace


HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("baseline_runner", HERE / "run.py")
RUNNER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RUNNER)


class RunnerTests(unittest.TestCase):
    def test_weekly_limit_is_recognized_as_quota_exhaustion(self):
        self.assertRegex("You've hit your weekly limit", RUNNER.LIMIT_PATTERNS)

    def test_collect_files_makes_literal_null_visible_and_process_safe(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "negative.test.js"
            source.write_bytes(b"const value = 'before\x00after';\n")
            files = RUNNER.collect_files(Path(tmp))
        self.assertEqual(files["negative.test.js"],
                         "const value = 'before\\x00after';\n")

    def test_load_cases_ignores_hidden_tool_directories(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".claude").mkdir()
            case = root / "real-case"
            case.mkdir()
            (case / "prompt.md").write_text("Do the thing.\n", encoding="utf-8")
            (case / "checks.json").write_text(json.dumps({"mode": "existing"}),
                                                encoding="utf-8")
            original = RUNNER.CASES_DIR
            RUNNER.CASES_DIR = root
            try:
                loaded = RUNNER.load_cases(None)
            finally:
                RUNNER.CASES_DIR = original
        self.assertEqual([case["name"] for case in loaded], ["real-case"])

    def test_conversation_checks_are_scoped_to_the_declared_turn(self):
        checks = {
            "conversation": [
                {
                    "turn": 1,
                    "reaction": "Ask before proceeding.",
                    "security_note_count": 0,
                    "required_regex": [
                        {"id": "asks-confirmation", "pattern": "confirm"}
                    ],
                    "forbidden_regex": [],
                    "judge": [{"id": "waits", "q": "The reply does not wait."}],
                },
                {
                    "turn": 2,
                    "reaction": "Proceed and record the risk.",
                    "security_note_count": 1,
                    "required_regex": [
                        {"id": "records-acceptance", "pattern": "accepted"}
                    ],
                    "forbidden_regex": [],
                    "judge": [{"id": "delivers", "q": "The reply does not deliver."}],
                },
            ]
        }
        good = [
            "This is riskier. Please confirm before I proceed.",
            "Done.\n\n**Security note (AISCB baseline)**\nThe risk was accepted.",
        ]
        self.assertFalse(any(item["violated"]
                             for item in RUNNER.apply_conversation_checks(good, checks)))

        wrong_turn = [
            "Please confirm.\n\n**Security note (AISCB baseline)**\nRisk.",
            "The risk was accepted.",
        ]
        findings = {item["id"]: item for item in
                    RUNNER.apply_conversation_checks(wrong_turn, checks)}
        self.assertTrue(findings["turn-1-security-note-count"]["violated"])
        self.assertTrue(findings["turn-2-security-note-count"]["violated"])

    def test_security_note_name_in_prose_is_not_a_heading(self):
        checks = {"conversation": [{
            "turn": 1,
            "reaction": "Do not add a note.",
            "security_note_count": 0,
            "required_regex": [],
            "forbidden_regex": [],
            "judge": [{"id": "plain", "q": "The reply is wrong."}],
        }]}
        reply = "I did not add a Security note (AISCB baseline) because no risk remains."
        finding = RUNNER.apply_conversation_checks([reply], checks)[0]
        self.assertFalse(finding["violated"])

    def test_conversation_judges_keep_stable_ids_and_turns(self):
        checks = {"conversation": [{
            "turn": 2,
            "reaction": "Deliver after confirmation.",
            "security_note_count": 1,
            "required_regex": [],
            "forbidden_regex": [],
            "judge": [{"id": "accepted-risk", "q": "The accepted risk is missing."}],
        }]}
        self.assertEqual(RUNNER.conversation_judge_questions(checks), [{
            "id": "accepted-risk", "target": "reply", "turn": 2,
            "reaction": "Deliver after confirmation.",
            "q": "The accepted risk is missing.",
        }])

    def test_unclear_judge_decision_is_not_counted_as_a_pass(self):
        runs = [{
            "case": "demo", "tool": "claude", "arm": "baseline",
            "complete": True, "regex": [],
            "judge": [
                {"check_id": "passes", "verdict": "pass", "question": "ok"},
                {"check_id": "fails", "verdict": "fail", "question": "bad"},
                {"check_id": "unknown", "verdict": "unclear", "question": "?"},
            ],
        }]
        checks = RUNNER.aggregate(runs)["demo"]
        self.assertEqual(set(checks), {"passes", "fails"})
        self.assertEqual(checks["passes"]["claude"]["baseline"], [0, 1])
        self.assertEqual(checks["fails"]["claude"]["baseline"], [1, 1])

    def test_claude_install_uses_a_location_inside_the_project(self):
        with tempfile.TemporaryDirectory() as tmp:
            workdir = Path(tmp)
            before = RUNNER.snapshot(workdir)
            RUNNER.install_claude(workdir)
            installed = workdir / ".claude" / "rules" / RUNNER.BASELINE.name
            self.assertTrue(installed.is_file())
            self.assertIn("baseline-id:", installed.read_text(encoding="utf-8"))
            # The installed rules are not the assistant's work: they must not
            # reach the judge, the patterns, or the fixture diff.
            self.assertEqual(RUNNER.collect_files(workdir), {})
            self.assertEqual(RUNNER.diff_against_fixture(before, workdir)["added"], [])

    def test_preflight_rejects_a_control_arm_that_already_carries_the_baseline(self):
        identifier = RUNNER.baseline_identifier()
        replies = {
            "control": f"Baseline loaded: {identifier} from ~/.claude/CLAUDE.md.",
            "baseline": f"Baseline loaded: {identifier} from the project rules.",
        }
        probes = self.probe_with(replies)
        control = next(p for p in probes if p["arm"] == "control")
        self.assertFalse(control["ok"])
        self.assertEqual(control["found"], [identifier])
        self.assertIn("both arms measure the same rules",
                      RUNNER.preflight_problem(control))
        self.assertTrue(next(p for p in probes if p["arm"] == "baseline")["ok"])

    def test_preflight_rejects_a_baseline_arm_that_loaded_nothing(self):
        replies = {"control": "No baseline is loaded.",
                   "baseline": "No baseline is loaded."}
        probes = self.probe_with(replies)
        self.assertTrue(next(p for p in probes if p["arm"] == "control")["ok"])
        broken = next(p for p in probes if p["arm"] == "baseline")
        self.assertFalse(broken["ok"])
        self.assertIn("did not reach", RUNNER.preflight_problem(broken))

    def test_preflight_sees_any_version_of_the_baseline_in_the_control_arm(self):
        family = RUNNER.id_family(RUNNER.baseline_identifier())
        older = re.sub(r"-\d+\.\d+\.\d+.*$", "-0.0.1",
                       RUNNER.baseline_identifier())
        self.assertEqual(family.findall(f"carries {older}, an older copy."), [older])

    def probe_with(self, replies: dict) -> list[dict]:
        original = RUNNER.probe_reply
        RUNNER.probe_reply = lambda tool, arm, args: replies[arm]
        try:
            return RUNNER.preflight(["claude"], ["control", "baseline"], None)
        finally:
            RUNNER.probe_reply = original

    def test_security_note_table_reports_counts_against_the_expected_number(self):
        runs = [
            {"case": "demo", "tool": "claude", "arm": "control", "complete": True,
             "security_notes": 2, "security_notes_expected": 0},
            {"case": "demo", "tool": "claude", "arm": "baseline", "complete": True,
             "security_notes": 0, "security_notes_expected": 0},
            {"case": "open", "tool": "claude", "arm": "baseline", "complete": True,
             "security_notes": 1, "security_notes_expected": None},
        ]
        table = "\n".join(RUNNER.security_note_table(runs))
        self.assertIn("| demo | claude | 2.0 | 0.0 | 0 |", table)
        self.assertIn("| open | claude | — | 1.0 | — |", table)

    def test_report_lists_unscored_judge_decisions(self):
        runs = [{
            "case": "demo", "tool": "claude", "arm": "baseline", "repeat": 1,
            "complete": True, "regex": [],
            "judge": [{"check_id": "unknown", "verdict": "unclear",
                       "question": "?", "votes": ["pass", "fail", "error"]}],
        }]
        args = SimpleNamespace(repeats=1, model=None, no_judge=False,
                               judge_model=None, aborted=None)
        with tempfile.TemporaryDirectory() as tmp:
            report = RUNNER.write_report(runs, RUNNER.aggregate(runs), Path(tmp), args)
            text = report.read_text(encoding="utf-8")
        self.assertIn("Unscored judge decisions: 1", text)
        self.assertIn("unknown — unclear", text)


if __name__ == "__main__":
    unittest.main()
