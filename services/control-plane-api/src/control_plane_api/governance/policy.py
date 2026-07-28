ALLOWED_TRANSITIONS: dict[str, list[str]] = {
    "discovered": ["registered", "retired"],
    "registered": ["assess", "retired"],
    "assess": ["build_test", "retired"],
    "build_test": ["steward_review", "retired"],
    "steward_review": ["shadow", "build_test", "retired"],
    "shadow": ["canary", "suspended", "retired"],
    "canary": ["production", "suspended", "retired"],
    "production": ["suspended", "retired"],
    "suspended": ["assess", "retired"],
    "retired": [],
}

REQUIRED_EVIDENCE: dict[str, set[str]] = {
    "build_test": {"risk_assessment"},
    "steward_review": {"test_report"},
    "shadow": {"risk_assessment", "test_report"},
    "canary": {"monitoring_plan"},
    "production": {"monitoring_plan", "rollback_plan"},
}
