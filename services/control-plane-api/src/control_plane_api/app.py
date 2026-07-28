from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.engine import Engine

from .database import build_engine, build_session_factory
from .models import Base
from .routers import agents, governance, mcp_gateway, platform, registry, runtime
from .seed import seed_demo_assets


def create_app(
    engine: Engine | None = None,
    *,
    seed_demo: bool | None = None,
) -> FastAPI:
    database_engine = engine or build_engine()
    session_factory = build_session_factory(database_engine)
    should_seed = (
        seed_demo
        if seed_demo is not None
        else os.getenv("NORTHSTAR_SEED_DEMO", "false").lower() == "true"
    )

    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        if os.getenv("NORTHSTAR_SCHEMA_MANAGEMENT", "create_all") == "create_all":
            Base.metadata.create_all(database_engine)
        application.state.session_factory = session_factory
        if should_seed:
            seed_demo_assets(session_factory)
        yield

    application = FastAPI(
        title="Northstar Control Plane",
        version="0.6.0",
        description="Governance API for A2A-ready agentic workflows.",
        lifespan=lifespan,
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    for router in (
        platform.router,
        registry.router,
        agents.router,
        governance.router,
        runtime.router,
        mcp_gateway.router,
    ):
        application.include_router(router)
    return application
