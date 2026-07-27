from typing import Literal

from pydantic import Field, model_validator

from .assets import AssetRef, AssetRegistration
from .base import ContractModel, Identifier, NonEmptyString
from .enums import AssetType


class WorkflowStage(ContractModel):
    stage_id: Identifier
    display_name: NonEmptyString
    agent: AssetRef | None = None
    human_review: bool = False
    allowed_mcp_tools: list[Identifier] = Field(default_factory=list)
    timeout_seconds: int = Field(default=60, ge=1, le=86_400)
    max_attempts: int = Field(default=1, ge=1, le=10)


class WorkflowManifest(AssetRegistration):
    asset_type: Literal[AssetType.AGENTIC_WORKFLOW] = AssetType.AGENTIC_WORKFLOW
    stages: list[WorkflowStage] = Field(min_length=1)
    participating_agents: list[AssetRef] = Field(default_factory=list)
    mcp_servers: list[AssetRef] = Field(default_factory=list)
    input_schema_ref: NonEmptyString
    output_schema_ref: NonEmptyString

    @model_validator(mode="after")
    def validate_unique_stages_and_agent_references(self) -> "WorkflowManifest":
        stage_ids = [stage.stage_id for stage in self.stages]
        if len(stage_ids) != len(set(stage_ids)):
            raise ValueError("workflow stage_id values must be unique")

        declared_agents = {
            (agent.asset_id, agent.version) for agent in self.participating_agents
        }
        undeclared = {
            (stage.agent.asset_id, stage.agent.version)
            for stage in self.stages
            if stage.agent is not None
            and (stage.agent.asset_id, stage.agent.version) not in declared_agents
        }
        if undeclared:
            raise ValueError(
                f"workflow stages reference undeclared agent versions: {sorted(undeclared)}"
            )
        return self
