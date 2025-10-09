"""FastAPI server demonstrating end-to-end agent integration.

Run with: uvicorn examples.fastapi_server:app --reload
Test with: curl -X POST http://localhost:8000/route -H "Content-Type: application/json" -d '{"request": "My invoice has extra charges"}'
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from pydantic import BaseModel

from agents.example.agent import ExampleAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global agent instance
agent: ExampleAgent | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize agent on startup."""
    global agent
    logger.info("Initializing ExampleAgent...")
    agent = ExampleAgent()
    yield
    logger.info("Shutting down...")


app = FastAPI(
    title="Observable Agent Starter - Example API",
    description="Production-ready FastAPI server with DSPy agent, Langfuse tracing, and DeepEval quality metrics",
    version="0.1.0",
    lifespan=lifespan,
)


class RouteRequest(BaseModel):
    request: str


class RouteResponse(BaseModel):
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


@app.post("/route", response_model=RouteResponse)
async def route_request(req: RouteRequest) -> RouteResponse:
    """
    Route an incoming request to the appropriate handler.

    - **request**: The user's request text

    Returns:
    - **route**: One of {billing, tech, sales}
    - **explanation**: Reasoning for the routing decision

    All requests are traced to Langfuse when credentials are configured.
    """
    if agent is None:
        raise RuntimeError("Agent not initialized")

    result = agent.forward(req.request)
    return RouteResponse(**result)


@app.get("/health")
async def health():
    """Detailed health check."""
    return {
        "agent_ready": agent is not None,
        "service": "observable-agent-starter",
    }
