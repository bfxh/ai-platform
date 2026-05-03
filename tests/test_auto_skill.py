"""Tests for auto_skill.py"""
import os
import sys
import tempfile
import json
import shutil

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.auto_skill import AutoSkillDetector, LearnedRuleEngine


class TestAutoSkillDetector:
    def setup_method(self):
        self.tmpdir = tempfile.mkdtemp()
        self.detector = AutoSkillDetector(history_dir=self.tmpdir)

    def teardown_method(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_record_task(self):
        self.detector.record_task(
            "code_review", {"file": "test.py"}, {"issues": 3}, success=True
        )
        files = list(os.listdir(self.tmpdir))
        assert len(files) == 1
        assert files[0].startswith("code_review_")

    def test_detect_pattern_below_threshold(self):
        for _ in range(2):
            self.detector.record_task(
                "test_task", {"input": "data"}, {"output": "result"}, success=True
            )
        pattern = self.detector.detect_repeated_pattern("test_task")
        assert pattern is None  # Below threshold of 3

    def test_detect_pattern_above_threshold(self):
        for _ in range(3):
            self.detector.record_task(
                "test_task", {"key": "value"}, {"output": "result"}, success=True
            )
        pattern = self.detector.detect_repeated_pattern("test_task")
        assert pattern is not None
        assert pattern["task_type"] == "test_task"
        assert pattern["occurrence_count"] == 3
        assert pattern["suggested_skill_name"] == "auto_test_task"

    def test_only_counts_successful(self):
        for _ in range(4):
            self.detector.record_task(
                "test_task", {"input": "data"}, {"output": "result"}, success=True
            )
        # Add failed records — should not count
        self.detector.record_task(
            "test_task", {"input": "data"}, {}, success=False
        )
        pattern = self.detector.detect_repeated_pattern("test_task")
        assert pattern["occurrence_count"] == 4

    def test_auto_generate_skill(self):
        for _ in range(3):
            self.detector.record_task(
                "code_review", {"language": "python"}, {"issues": 0}, success=True
            )

        skill_dir = os.path.join(self.tmpdir, "skills")
        skill_path = self.detector.auto_generate_skill("code_review", skill_dir)

        assert skill_path is not None
        assert os.path.exists(skill_path)

        with open(skill_path) as f:
            skill = json.load(f)
        assert skill["name"] == "auto_code_review"
        assert skill["auto_generated"] is True
        assert "language" in skill["inputs"]


class TestLearnedRuleEngine:
    def setup_method(self):
        self.engine = LearnedRuleEngine()

    def test_learn_from_failure(self):
        rule = self.engine.learn_from_failure(
            "code_generation",
            "SyntaxError: invalid syntax at line 42",
            "Add syntax validation before execution",
        )
        assert rule["task_type"] == "code_generation"
        assert rule["confidence"] == 0.0
        assert rule["auto_apply"] is False

    def test_match_rule_no_match(self):
        self.engine.learn_from_failure(
            "task_a", "error pattern X", "fix A"
        )
        result = self.engine.match_rule("completely different error", 0.8)
        assert result is None

    def test_match_rule_below_confidence(self):
        self.engine.learn_from_failure(
            "task_a", "syntax error", "check syntax"
        )
        # Confidence is 0, below 0.8 threshold
        result = self.engine.match_rule("syntax error occurred", 0.8)
        assert result is None

    def test_confidence_increases_to_auto_apply(self):
        rule = self.engine.learn_from_failure(
            "task_a", "out of memory", "increase memory limit"
        )
        idx = 0

        # Apply successfully multiple times
        for _ in range(10):
            self.engine.update_rule_success(idx, success=True)

        updated_rule = self.engine._rules[idx]
        assert updated_rule["confidence"] > 0.8
        assert updated_rule["auto_apply"] is True

    def test_failure_decreases_confidence(self):
        rule = self.engine.learn_from_failure(
            "task_b", "timeout error", "increase timeout"
        )
        idx = 0

        # Some successes
        for _ in range(3):
            self.engine.update_rule_success(idx, success=True)

        # Then a failure
        self.engine.update_rule_success(idx, success=False)
        updated_rule = self.engine._rules[idx]
        assert updated_rule["confidence"] < 1.0
