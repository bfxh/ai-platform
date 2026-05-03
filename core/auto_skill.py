"""
Auto-skill detection and generation.
Detects repeated successful task patterns and automatically generates
reusable Skill definitions for the Multica platform.
"""
import json
import os
import logging
from collections import defaultdict
from pathlib import Path
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class AutoSkillDetector:
    """
    Detects repeated successful task execution patterns and
    proposes auto-generated Skills.
    """

    def __init__(self, history_dir: str = None):
        self.history_dir = Path(history_dir) if history_dir else Path(".agent_history")
        self.history_dir.mkdir(parents=True, exist_ok=True)
        self._pattern_threshold = 3  # Minimum repeats to trigger auto-skill

    def record_task(self, task_type: str, task_input: dict, task_output: dict, success: bool) -> None:
        record = {
            "task_type": task_type,
            "input": task_input,
            "output": task_output,
            "success": success,
            "timestamp": datetime.now().isoformat(),
        }
        ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        record_file = self.history_dir / f"{task_type}_{ts}.json"
        with open(record_file, "w") as f:
            json.dump(record, f, indent=2)

    def detect_repeated_pattern(self, task_type: str) -> Optional[dict]:
        """Detect if a task type has been repeated successfully >= threshold times."""
        records = []
        for f in self.history_dir.glob(f"{task_type}_*.json"):
            try:
                with open(f, "r") as fp:
                    data = json.load(fp)
                    if data.get("success"):
                        records.append(data)
            except Exception:
                pass

        if len(records) < self._pattern_threshold:
            return None

        # Extract common input patterns
        common_inputs = self._extract_common_input_patterns(records)

        return {
            "task_type": task_type,
            "occurrence_count": len(records),
            "common_inputs": common_inputs,
            "suggested_skill_name": f"auto_{task_type}",
        }

    def _extract_common_input_patterns(self, records: list) -> dict:
        """Extract commonly occurring input keys and their typical values."""
        key_counts = defaultdict(list)
        for record in records:
            inp = record.get("input", {})
            for k, v in inp.items():
                key_counts[k].append(v)

        common = {}
        for k, values in key_counts.items():
            if len(values) >= self._pattern_threshold:
                # Return the most common value
                from collections import Counter
                most_common = Counter([str(v) for v in values]).most_common(1)[0][0]
                common[k] = most_common
        return common

    def auto_generate_skill(self, task_type: str, skill_dir: str = None) -> Optional[str]:
        """
        Auto-generate a Skill definition from repeated task patterns.
        Returns the skill file path if generated, None otherwise.
        """
        pattern = self.detect_repeated_pattern(task_type)
        if pattern is None:
            return None

        skill_dir = Path(skill_dir) if skill_dir else Path("skills")
        skill_dir.mkdir(parents=True, exist_ok=True)

        skill_name = pattern["suggested_skill_name"]
        skill_file = skill_dir / f"{skill_name}.json"

        skill_def = {
            "name": skill_name,
            "description": f"Auto-generated skill for {task_type} (from {pattern['occurrence_count']} successful runs)",
            "task_type": task_type,
            "auto_generated": True,
            "inputs": pattern["common_inputs"],
            "generated_at": datetime.now().isoformat(),
        }

        with open(skill_file, "w") as f:
            json.dump(skill_def, f, indent=2)

        logger.info(f"Auto-generated skill: {skill_name} ({skill_file})")
        return str(skill_file)


class LearnedRuleEngine:
    """
    Learned rules for automatic task retry with strategy matching.
    Integrates with the Go backend's learned_rule table.
    """

    def __init__(self):
        self._rules: list = []

    def learn_from_failure(self, task_type: str, error_message: str, fix_strategy: str) -> dict:
        rule = {
            "task_type": task_type,
            "error_pattern": error_message[:200],
            "fix_strategy": fix_strategy,
            "success_count": 0,
            "total_attempts": 1,
            "confidence": 0.0,
            "auto_apply": False,
            "created_at": datetime.now().isoformat(),
        }
        self._rules.append(rule)
        logger.info(f"Rule learned for {task_type}: {fix_strategy[:50]}...")
        return rule

    def match_rule(self, error_message: str, min_confidence: float = 0.8) -> Optional[dict]:
        for rule in sorted(self._rules, key=lambda r: r["confidence"], reverse=True):
            if rule["auto_apply"] and rule["confidence"] >= min_confidence:
                if rule["error_pattern"].lower() in error_message.lower():
                    return rule
        return None

    def update_rule_success(self, rule_index: int, success: bool) -> None:
        if 0 <= rule_index < len(self._rules):
            rule = self._rules[rule_index]
            rule["total_attempts"] += 1
            if success:
                rule["success_count"] += 1
            rule["confidence"] = rule["success_count"] / max(rule["total_attempts"], 1)
            rule["auto_apply"] = rule["confidence"] >= 0.8
