"""Governance guards for prompt injection, data leakage, and access control."""

import re
from dataclasses import dataclass

import structlog

from app.config import Settings
from app.models.schemas import GovernanceCheck, GovernanceResult

logger = structlog.get_logger()


@dataclass
class GuardResult:
    passed: bool
    reason: str = ""
    severity: str = "info"


class GovernanceGuard:
    """
    Enforces AI governance policies on incoming requests and agent outputs.

    Policies: prompt injection detection, PII filtering, content moderation,
    token budget enforcement, and tool access validation.
    """

    INJECTION_PATTERNS = [
        r"ignore\s+(all\s+)?previous\s+instructions",
        r"disregard\s+(all\s+)?prior",
        r"you\s+are\s+now\s+a",
        r"system\s*:\s*",
        r"<\s*/?\s*script",
        r"jailbreak",
        r"DAN\s+mode",
    ]

    PII_PATTERNS = [
        r"\b\d{3}-\d{2}-\d{4}\b",  # SSN
        r"\b\d{16}\b",  # Credit card
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",  # Email (warn only)
    ]

    BLOCKED_TOPICS = [
        "generate malware",
        "bypass security",
        "extract passwords",
    ]

    def __init__(self, settings: Settings):
        self.settings = settings
        self._injection_re = [re.compile(p, re.IGNORECASE) for p in self.INJECTION_PATTERNS]
        self._pii_re = [re.compile(p) for p in self.PII_PATTERNS]

    def audit_request(self, query: str) -> GovernanceResult:
        """Run all governance checks and return a structured audit result."""
        checks: list[GovernanceCheck] = []

        length_ok = len(query) <= 4000
        checks.append(
            GovernanceCheck(
                name="query_length",
                passed=length_ok,
                reason="" if length_ok else "Query exceeds maximum length (4000 chars)",
            )
        )

        injection_ok = True
        injection_reason = ""
        for pattern in self._injection_re:
            if pattern.search(query):
                logger.warning("injection_detected", pattern=pattern.pattern)
                injection_ok = False
                injection_reason = "Potential prompt injection detected"
                break
        checks.append(
            GovernanceCheck(
                name="prompt_injection",
                passed=injection_ok,
                reason=injection_reason,
            )
        )

        blocked_ok = True
        blocked_reason = ""
        query_lower = query.lower()
        for topic in self.BLOCKED_TOPICS:
            if topic in query_lower:
                blocked_ok = False
                blocked_reason = f"Blocked topic detected: {topic}"
                break
        checks.append(
            GovernanceCheck(
                name="blocked_topics",
                passed=blocked_ok,
                reason=blocked_reason,
            )
        )

        pii_ok = True
        pii_reason = ""
        for pattern in self._pii_re[:2]:
            if pattern.search(query):
                pii_ok = False
                pii_reason = "Potential PII detected in query — please redact sensitive data"
                break
        checks.append(
            GovernanceCheck(
                name="pii_detection",
                passed=pii_ok,
                reason=pii_reason,
            )
        )

        return GovernanceResult(passed=all(c.passed for c in checks), checks=checks)

    def validate_request(self, query: str) -> GuardResult:
        """Validate incoming user request against governance policies."""
        audit = self.audit_request(query)
        if not audit.passed:
            failed = next(c for c in audit.checks if not c.passed)
            severity = "critical" if failed.name in {"prompt_injection", "blocked_topics"} else "warning"
            return GuardResult(passed=False, reason=failed.reason, severity=severity)
        return GuardResult(passed=True)

    def validate_token_budget(self, tokens_used: int) -> GuardResult:
        """Check if token usage is within budget."""
        if tokens_used > self.settings.token_budget_per_request:
            return GuardResult(
                passed=False,
                reason=f"Token budget exceeded: {tokens_used}/{self.settings.token_budget_per_request}",
                severity="warning",
            )
        return GuardResult(passed=True)

    def sanitize_output(self, text: str) -> str:
        """Remove potential data leakage from agent outputs."""
        for pattern in self._pii_re[:2]:
            text = pattern.sub("[REDACTED]", text)
        return text
