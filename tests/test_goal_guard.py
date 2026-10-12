"""Black-box regression tests for route gates and original Vibe Guard checks."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "vibe-guard" / "scripts"


class GoalGuardTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.work = Path(self.tmp.name) / "project"
        self.work.mkdir()
        self.git("init", "-q")
        self.git("config", "user.email", "tests@example.invalid")
        self.git("config", "user.name", "Test")
        (self.work / "app.txt").write_text("initial\n", encoding="utf8")
        self.git("add", "app.txt")
        self.git("commit", "-qm", "init")

    def git(self, *args: str) -> None:
        subprocess.run(["git", "-C", str(self.work), *args], check=True, capture_output=True)

    def cmd(self, script: str, *args: str, expected: int = 0) -> dict:
        argv = [sys.executable, str(SCRIPTS / script)]
        if script == "goal_guard.py":
            argv += [args[0], str(self.work), *args[1:]]
        else:
            argv += [str(self.work), *args]
        p = subprocess.run(argv, text=True, capture_output=True)
        if p.returncode != expected:
            self.fail(f"{script} code={p.returncode}, expected={expected}\nstdout:{p.stdout}\nstderr:{p.stderr}")
        if p.stdout.strip().startswith("{"):
            return json.loads(p.stdout)
        return {"stdout": p.stdout.strip(), "stderr": p.stderr.strip()}

    def goal(self) -> None:
        self.cmd("goal_guard.py", "goal-set", "--outcome", "Ship one usable screen", "--success", "An end user completes the main action", "--non-goal", "No account system", "--stop-condition", "Stop if no one can use it")

    def open(self, trigger="milestone") -> str:
        return self.cmd("goal_guard.py", "review-open", "--trigger", trigger, "--proposal", "Finish the main journey")["review_id"]

    def close(self, review_id: str, verdict: str = "continue", reviewer="self") -> None:
        command = ["review-close", review_id, "--verdict", verdict, "--reviewer", reviewer,
                   "--evidence", "Observed a completed task with the current artifact", "--alternative", "Use one screen instead of multiple features", "--remaining-cost", "One more real-use check", "--rationale", "Main journey worked"]
        if verdict != "continue":
            command += ["--next-action", "Remove unnecessary features first"]
        self.cmd("goal_guard.py", *command)

    def test_backward_compatible_routine_gate_without_goal(self) -> None:
        got = self.cmd("check_gate.py")
        self.assertTrue(got["ok"])
        self.assertTrue(any(x["kind"] == "goal_contract_not_initialized_legacy_compatible" for x in got["warnings"]))
        failed = self.cmd("check_gate.py", "--phase", "release", expected=2)
        self.assertIn("goal_contract_missing", [x["kind"] for x in failed["blocks"]])

    def test_contract_is_immutable_without_user_authorized_revision(self) -> None:
        self.goal()
        self.cmd("goal_guard.py", "goal-set", "--outcome", "Anything else", "--success", "different", expected=1)
        self.cmd("goal_guard.py", "goal-amend", "--outcome", "Now ship two screens", "--success", "Two journeys work", "--user-quote", "", "--reason", "New requirement", expected=1)
        self.cmd("goal_guard.py", "goal-amend", "--outcome", "Now ship two screens", "--success", "Two journeys work", "--user-quote", "Please add a second screen", "--reason", "User revised target")
        result = self.cmd("goal_guard.py", "goal-show")
        self.assertEqual(result["original"]["outcome"], "Ship one usable screen")
        self.assertEqual(result["active"]["outcome"], "Now ship two screens")
        self.assertEqual(result["active"]["version"], 2)
        self.assertEqual(result["active"]["non_goals"], ["No account system"])

    def test_milestone_requires_fresh_review_bound_to_actual_files(self) -> None:
        self.goal()
        failed = self.cmd("check_gate.py", "--phase", "milestone", expected=2)
        self.assertIn("fresh_route_review_required", [x["kind"] for x in failed["blocks"]])
        rid = self.open()
        prompt = self.cmd("goal_guard.py", "goal-show")
        self.assertEqual(prompt["original"]["outcome"], "Ship one usable screen")
        self.cmd("check_gate.py", "--phase", "milestone", expected=2)
        self.close(rid)
        passed = self.cmd("check_gate.py", "--phase", "milestone")
        self.assertTrue(passed["ok"])
        (self.work / "app.txt").write_text("changed\n", encoding="utf8")
        failed = self.cmd("check_gate.py", "--phase", "milestone", expected=2)
        self.assertIn("fresh_route_review_required", [x["kind"] for x in failed["blocks"]])

    def test_change_during_review_invalidates_completion(self) -> None:
        self.goal()
        rid = self.open()
        (self.work / "file2.txt").write_text("new untracked content", encoding="utf8")
        self.cmd("goal_guard.py", "review-close", rid, "--verdict", "continue", "--reviewer", "self", "--evidence", "A passing run", "--alternative", "Smaller route", "--remaining-cost", "One check", "--rationale", "Meets goal", expected=1)
        result = self.cmd("check_gate.py", "--phase", "milestone", expected=2)
        self.assertIn("route_review_open", [x["kind"] for x in result["blocks"]])

    def test_hold_needs_action_resolution_and_new_review(self) -> None:
        self.goal()
        rid = self.open("architecture")
        self.close(rid, "redirect")
        result = self.cmd("check_gate.py", expected=2)
        self.assertIn("route_review_requires_action", [x["kind"] for x in result["blocks"]])
        self.cmd("goal_guard.py", "review-resolve", rid, "--resolution", "Done", "--evidence", "No changes", expected=1)
        (self.work / "app.txt").write_text("simpler\n", encoding="utf8")
        self.cmd("goal_guard.py", "review-resolve", rid, "--resolution", "Simplified implementation", "--evidence", "Deleted an unnecessary step")
        self.assertTrue(self.cmd("check_gate.py")["ok"])
        self.cmd("check_gate.py", "--phase", "milestone", expected=2)
        rid2 = self.open("milestone")
        self.close(rid2)
        self.assertTrue(self.cmd("check_gate.py", "--phase", "milestone")["ok"])

    def test_release_requires_release_trigger_and_revision_invalidates_old_pass(self) -> None:
        self.goal()
        rid = self.open("milestone")
        self.close(rid)
        self.assertTrue(self.cmd("check_gate.py", "--phase", "milestone")["ok"])
        self.cmd("check_gate.py", "--phase", "release", expected=2)
        release = self.open("release")
        self.close(release, reviewer="independent")
        passed = self.cmd("check_gate.py", "--phase", "release")
        self.assertTrue(passed["ok"])
        self.assertIn("reviewer_independence_declared_not_technically_verified", [x["kind"] for x in passed["warnings"]])
        self.cmd("goal_guard.py", "goal-amend", "--outcome", "Ship two screens", "--success", "Both screens work", "--user-quote", "Make the second screen", "--reason", "Changed acceptance")
        result = self.cmd("check_gate.py", "--phase", "release", expected=2)
        self.assertIn("fresh_route_review_required", [x["kind"] for x in result["blocks"]])

    def test_old_continue_cannot_override_new_hold_on_unchanged_workspace(self) -> None:
        self.goal()
        first = self.open("milestone")
        self.close(first)
        self.assertTrue(self.cmd("check_gate.py", "--phase", "milestone")["ok"])

        later = self.open("architecture")
        self.close(later, "redirect")
        self.cmd("check_gate.py", "--phase", "milestone", expected=2)
        # The claimed user quote permits marking the hold addressed without
        # modifying the artifact, but it must NOT resurrect the old pass.
        self.cmd("goal_guard.py", "review-resolve", later,
                 "--resolution", "User clarified that unchanged design is desired",
                 "--evidence", "New user preference", "--user-quote", "Please keep the layout")
        result = self.cmd("check_gate.py", "--phase", "milestone", expected=2)
        self.assertIn("fresh_route_review_required", [x["kind"] for x in result["blocks"]])
        new = self.open("milestone")
        self.close(new)
        self.assertTrue(self.cmd("check_gate.py", "--phase", "milestone")["ok"])

    def test_review_must_record_alternative_and_real_evidence(self) -> None:
        self.goal()
        rid = self.open()
        self.cmd("goal_guard.py", "review-close", rid, "--verdict", "continue",
                 "--reviewer", "self", "--evidence", "Only activity completed",
                 "--alternative", " ", "--remaining-cost", "Some cost",
                 "--rationale", "Done", expected=1)
        self.cmd("check_gate.py", "--phase", "milestone", expected=2)
        self.close(rid)
        self.assertTrue(self.cmd("check_gate.py", "--phase", "milestone")["ok"])

    def test_stop_requires_explicit_user_instruction_for_resolution(self) -> None:
        self.goal()
        rid = self.open("repeated_failure")
        self.close(rid, "stop")
        (self.work / "app.txt").write_text("new approach\n", encoding="utf8")
        self.cmd("goal_guard.py", "review-resolve", rid, "--resolution", "ignored", "--evidence", "Changed file", expected=1)
        self.cmd("goal_guard.py", "review-resolve", rid, "--resolution", "User asked for a different direction", "--evidence", "New user request", "--user-quote", "Try a smaller option")
        self.cmd("check_gate.py", "--phase", "milestone", expected=2)


if __name__ == "__main__":
    unittest.main()
