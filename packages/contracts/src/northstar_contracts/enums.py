from enum import StrEnum


class AssetType(StrEnum):
    AI_SYSTEM = "ai_system"
    AGENTIC_WORKFLOW = "agentic_workflow"
    AGENT = "agent"
    MODEL = "model"
    PROMPT = "prompt"
    DATASET = "dataset"
    KNOWLEDGE_INDEX = "knowledge_index"
    MCP_SERVER = "mcp_server"


class GovernanceState(StrEnum):
    DISCOVERED = "discovered"
    REGISTERED = "registered"
    ASSESS = "assess"
    BUILD_TEST = "build_test"
    STEWARD_REVIEW = "steward_review"
    SHADOW = "shadow"
    CANARY = "canary"
    PRODUCTION = "production"
    SUSPENDED = "suspended"
    RETIRED = "retired"


class RiskLevel(StrEnum):
    UNASSESSED = "unassessed"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    UNACCEPTABLE = "unacceptable"


class RunStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    WAITING_FOR_HUMAN = "waiting_for_human"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class RuntimeEventType(StrEnum):
    RUN_STARTED = "run.started"
    STAGE_STARTED = "stage.started"
    STAGE_COMPLETED = "stage.completed"
    RUN_WAITING_FOR_HUMAN = "run.waiting_for_human"
    HUMAN_DECISION_RECORDED = "human.decision.recorded"
    TOOL_REQUESTED = "tool.requested"
    TOOL_ALLOWED = "tool.allowed"
    TOOL_DENIED = "tool.denied"
    RUN_RESUMED = "run.resumed"
    RUN_FAILED = "run.failed"
    RUN_COMPLETED = "run.completed"


class ReviewDecision(StrEnum):
    APPROVE = "approve"
    REJECT = "reject"
    REQUEST_CHANGES = "request_changes"

