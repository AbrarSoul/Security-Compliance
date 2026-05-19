"""Threat types and scoring (Sprint 3 Step 9)."""

THREAT_REPEATED_POLICY_VIOLATION = "repeated_policy_violation"
THREAT_SUSPICIOUS_PROMPT = "suspicious_prompt_activity"
THREAT_EXCESSIVE_BLOCKS = "excessive_blocked_requests"
THREAT_ABNORMAL_EXECUTION = "abnormal_execution_behavior"
THREAT_EXTERNAL_API_ABUSE = "repeated_external_api_abuse"
THREAT_PROMPT_INJECTION = "prompt_injection_attack"
THREAT_JAILBREAK = "jailbreak_attempt"

CATEGORY_PROMPT_SECURITY = "prompt_security"
CATEGORY_EXECUTION = "execution"
CATEGORY_POLICY = "policy"
CATEGORY_API_ABUSE = "api_abuse"

SEVERITY_CRITICAL = "critical"
SEVERITY_HIGH = "high"
SEVERITY_MEDIUM = "medium"
SEVERITY_LOW = "low"

THREAT_STATUS_OPEN = "open"
THREAT_STATUS_INVESTIGATING = "investigating"
THREAT_STATUS_RESOLVED = "resolved"
THREAT_STATUS_FALSE_POSITIVE = "false_positive"

SEVERITY_BASE_SCORE: dict[str, int] = {
    SEVERITY_CRITICAL: 92,
    SEVERITY_HIGH: 78,
    SEVERITY_MEDIUM: 58,
    SEVERITY_LOW: 38,
}

WINDOW_HOURS = 24
POLICY_VIOLATION_THRESHOLD = 3
BLOCKED_REQUEST_THRESHOLD = 5
EXTERNAL_API_ABUSE_THRESHOLD = 3
EXECUTION_BURST_THRESHOLD = 10

SECURITY_EVENT_THREAT_DETECTED = "security.threat.detected"
SECURITY_EVENT_ANALYSIS_RUN = "security.analysis.run"
