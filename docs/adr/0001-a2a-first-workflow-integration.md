# ADR 0001: A2A-first workflow integration

## Status

Accepted for the foundation milestone.

## Decision

Every independently deployable agent exposes an official A2A Agent Card and A2A
task endpoint. Northstar stores governance metadata around the card but does not
fork or reimplement the A2A protocol schema.

Every LangGraph workflow is registered as a versioned `agentic_workflow` asset.
Its manifest references versioned agents and MCP servers, declares stages and
human-review interrupts, and provides input/output schema references.

The workflow integration SDK will emit the canonical runtime events defined in
`northstar_contracts.runtime`. Those events power Runtime Operations without
workflow-specific portal code.

## Required correlations

Every workflow run carries:

- Northstar workflow run ID
- LangGraph thread ID
- OpenTelemetry trace ID
- A2A task IDs
- MCP request IDs
- Optional Langfuse trace ID

## Enforcement boundary

A2A describes agent discovery and task communication. It does not grant tool
authority. ContextForge and Keycloak will enforce MCP tool access separately.
Human approval will produce a request-bound, short-lived capability rather than
granting an agent a reusable privilege.

## Fixture mode

The foundation operates without an AI model endpoint. Fixture agents still use
the same A2A registration, workflow manifests, runtime events and human-review
contracts that real agents will use later.
