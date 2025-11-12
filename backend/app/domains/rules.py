"""
Conflict rule template and management system for domains.

Handles loading, validating, and serving domain-specific conflict rules
from configuration files (JSON, etc).
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.base import ConflictRule

logger = logging.getLogger(__name__)


class ConflictRuleEngine:
    """
    Engine for managing domain conflict detection rules.

    Loads rules from configuration files and provides filtering,
    validation, and rule management capabilities.

    Usage:
        engine = ConflictRuleEngine()
        rules = engine.load_rules("domains/programming/rules.json")
        error_rules = engine.filter_by_severity(rules, "error")
    """

    def __init__(self):
        """Initialize the conflict rule engine."""
        self.rules_cache: Dict[str, List[ConflictRule]] = {}

    def load_rules_from_dict(self, data: List[Dict[str, Any]]) -> List[ConflictRule]:
        """
        Load conflict rules from a list of dictionaries.

        Args:
            data: List of rule dictionaries

        Returns:
            List of ConflictRule objects

        Example:
            data = [
                {
                    "rule_id": "perf_conflict",
                    "name": "Performance Consistency",
                    "description": "Response time requirements must be consistent",
                    "condition": "response_time specifications must not contradict",
                    "severity": "error",
                    "message": "Conflicting response time specifications"
                },
                ...
            ]
            rules = engine.load_rules_from_dict(data)
        """
        rules = []

        for item in data:
            try:
                # Import here to avoid circular imports
                from app.base import SeverityLevel

                severity_str = item.get("severity", "error").upper()
                severity = SeverityLevel[severity_str]

                rule = ConflictRule(
                    rule_id=item.get("rule_id"),
                    name=item.get("name"),
                    description=item.get("description"),
                    condition=item.get("condition"),
                    severity=severity,
                    message=item.get("message"),
                )
                rules.append(rule)
                logger.debug(f"Loaded rule: {rule.rule_id}")
            except (KeyError, ValueError) as e:
                logger.error(f"Error loading rule {item.get('rule_id', '?')}: {e}")
                raise ValueError(f"Invalid rule configuration: {e}")

        return rules

    def load_rules_from_json(self, json_file: str) -> List[ConflictRule]:
        """
        Load conflict rules from a JSON file.

        Args:
            json_file: Path to JSON file

        Returns:
            List of ConflictRule objects
        """
        path = Path(json_file)
        if not path.exists():
            raise FileNotFoundError(f"Rules file not found: {json_file}")

        with open(path, "r") as f:
            data = json.load(f)

        if not isinstance(data, list):
            raise ValueError("Rules file must contain a JSON array")

        return self.load_rules_from_dict(data)

    def filter_by_severity(self, rules: List[ConflictRule], severity: str) -> List[ConflictRule]:
        """
        Filter rules by severity level.

        Args:
            rules: List of rules
            severity: Severity level to filter by (error, warning, info)

        Returns:
            Filtered rules
        """
        from app.base import SeverityLevel

        try:
            severity_level = SeverityLevel[severity.upper()]
        except KeyError:
            return []

        return [r for r in rules if r.severity == severity_level]

    def filter_by_category(self, rules: List[ConflictRule], category: str) -> List[ConflictRule]:
        """
        Filter rules by category (based on rule_id prefix).

        Args:
            rules: List of rules
            category: Category to filter by (perf, sec, scale, arch, etc)

        Returns:
            Filtered rules

        Categories:
        - perf: Performance-related rules
        - sec: Security-related rules
        - scale: Scalability-related rules
        - arch: Architecture-related rules
        - data: Data-related rules
        - comply: Compliance-related rules
        """
        return [r for r in rules if r.rule_id.startswith(category.lower())]

    def filter_by_pattern(self, rules: List[ConflictRule], pattern: str) -> List[ConflictRule]:
        """
        Filter rules by pattern matching in name or description.

        Args:
            rules: List of rules
            pattern: Pattern to search for (case-insensitive)

        Returns:
            Filtered rules
        """
        pattern_lower = pattern.lower()
        return [
            r
            for r in rules
            if pattern_lower in r.name.lower() or pattern_lower in r.description.lower()
        ]

    def validate_rules(self, rules: List[ConflictRule]) -> List[str]:
        """
        Validate a set of rules for correctness.

        Checks for:
        - Duplicate rule IDs
        - Invalid severity levels
        - Missing required fields
        - Invalid conditions

        Args:
            rules: List of rules to validate

        Returns:
            List of validation error messages (empty if valid)

        Example:
            errors = engine.validate_rules(rules)
            if errors:
                for error in errors:
                    print(f"Validation error: {error}")
        """
        errors = []

        # Check for duplicate IDs
        rule_ids = [r.rule_id for r in rules]
        duplicates = [id for id in rule_ids if rule_ids.count(id) > 1]
        if duplicates:
            errors.append(f"Duplicate rule IDs: {set(duplicates)}")

        # Check for required fields
        for r in rules:
            if not r.rule_id:
                errors.append("Rule missing rule_id")
            if not r.name:
                errors.append(f"Rule {r.rule_id} missing name")
            if not r.description:
                errors.append(f"Rule {r.rule_id} missing description")
            if not r.condition:
                errors.append(f"Rule {r.rule_id} missing condition")
            if not r.message:
                errors.append(f"Rule {r.rule_id} missing message")

        # Validate severity is set
        from .base import SeverityLevel

        for r in rules:
            if not isinstance(r.severity, SeverityLevel):
                errors.append(f"Rule {r.rule_id} has invalid severity: {r.severity}")

        return errors

    def get_rules_by_category(self, rules: List[ConflictRule]) -> Dict[str, List[ConflictRule]]:
        """
        Group rules by category (based on rule_id prefix).

        Returns:
            Dictionary mapping categories to rules
        """
        categories = {}
        for r in rules:
            # Extract category from rule_id (e.g., "perf" from "perf_conflict")
            parts = r.rule_id.split("_")
            category = parts[0] if parts else "other"
            if category not in categories:
                categories[category] = []
            categories[category].append(r)
        return categories

    def get_rules_by_severity(self, rules: List[ConflictRule]) -> Dict[str, List[ConflictRule]]:
        """
        Group rules by severity level.

        Returns:
            Dictionary mapping severity levels to rules
        """
        from .base import SeverityLevel

        severity_groups = {
            "error": [],
            "warning": [],
            "info": [],
        }

        for r in rules:
            if r.severity == SeverityLevel.ERROR:
                severity_groups["error"].append(r)
            elif r.severity == SeverityLevel.WARNING:
                severity_groups["warning"].append(r)
            elif r.severity == SeverityLevel.INFO:
                severity_groups["info"].append(r)

        # Remove empty groups
        return {k: v for k, v in severity_groups.items() if v}

    def to_dict(self, rules: List[ConflictRule]) -> List[Dict[str, Any]]:
        """Convert rules to dictionary representation."""
        return [
            {
                "rule_id": r.rule_id,
                "name": r.name,
                "description": r.description,
                "condition": r.condition,
                "severity": r.severity.name.lower(),
                "message": r.message,
            }
            for r in rules
        ]

    def to_json(self, rules: List[ConflictRule]) -> str:
        """Convert rules to JSON string."""
        return json.dumps(self.to_dict(rules), indent=2)

    def save_to_json(self, rules: List[ConflictRule], filepath: str) -> None:
        """
        Save rules to a JSON file.

        Args:
            rules: Rules to save
            filepath: Path to save file
        """
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w") as f:
            f.write(self.to_json(rules))

        logger.info(f"Saved {len(rules)} conflict rules to {filepath}")


# Global conflict rule engine instance
_global_engine: Optional[ConflictRuleEngine] = None


def get_rule_engine() -> ConflictRuleEngine:
    """Get the global conflict rule template engine."""
    global _global_engine
    if _global_engine is None:
        _global_engine = ConflictRuleEngine()
    return _global_engine
