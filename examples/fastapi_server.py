"""FastAPI server demonstrating end-to-end triage agent integration.

Run with: uvicorn examples.fastapi_server:app --reload
Test with: curl -X POST http://localhost:8000/triage -H "Content-Type: application/json" -d '{"ticket": "My invoice has extra charges"}'
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from pydantic import BaseModel

from agents.triage.agent import TriageAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global agent instance
agent: TriageAgent | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize agent on startup."""
    global agent
    logger.info("Initializing TriageAgent...")
    agent = TriageAgent()
    yield
    logger.info("Shutting down...")


app = FastAPI(
    title="Observable Agent Starter - Triage API",
    description="Production-ready FastAPI server with DSPy triage agent, Langfuse tracing, and DeepEval quality metrics",
    version="0.1.0",
    lifespan=lifespan,
)


class TriageRequest(BaseModel):
    ticket: str


class TriageResponse(BaseModel):
    route: str
    explanation: str


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "service": "observable-agent-starter",
        "status": "ok",
        "version": "0.1.0",
    }


@app.post("/triage", response_model=TriageResponse)
async def triage(request: TriageRequest) -> TriageResponse:
    """
    Route a support ticket to the appropriate team.

    - **ticket**: The user's support ticket text

    Returns:
    - **route**: One of {billing, tech, sales}
    - **explanation**: Reasoning for the routing decision

    All requests are traced to Langfuse when credentials are configured.
    """
    if agent is None:
        raise RuntimeError("Agent not initialized")

    result = agent.forward(request.ticket)
    return TriageResponse(**result)


@app.get("/health")
async def health():
    """Detailed health check."""
    return {
        "agent_ready": agent is not None,
        "service": "observable-agent-starter",
    }
