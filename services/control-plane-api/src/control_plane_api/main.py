from fastapi import FastAPI

from northstar_contracts import AgentRegistration, RuntimeEvent, WorkflowManifest

app = FastAPI(
    title="Northstar Control Plane",
    version="0.1.0",
    description="Governance API for A2A-ready agentic workflows.",
)


@app.get("/healthz", tags=["platform"])
def health() -> dict[str, str]:
    return {"status": "ok", "mode": "fixture"}


@app.get("/api/v1/meta/capabilities", tags=["platform"])
def capabilities() -> dict[str, object]:
    return {
        "a2a_registration": True,
        "workflow_manifests": True,
        "runtime_events": True,
        "model_provider": "not_configured",
        "persistence": "not_configured",
    }


@app.post("/api/v1/agents/validate", tags=["registry"])
def validate_agent(agent: AgentRegistration) -> AgentRegistration:
    return agent


@app.post("/api/v1/workflows/validate", tags=["registry"])
def validate_workflow(workflow: WorkflowManifest) -> WorkflowManifest:
    return workflow


@app.post("/api/v1/runtime/events/validate", tags=["runtime"])
def validate_runtime_event(event: RuntimeEvent) -> RuntimeEvent:
    return event

