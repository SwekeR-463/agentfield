"""Generalized Multi-Agent Simulation System.

A domain-agnostic simulation engine that can model any enterprise scenario using
LLM-powered multi-reasoner architecture with maximum parallelism.
"""

from __future__ import annotations

import os
from pathlib import Path
import sys

from agentfield import AIConfig, Agent

if __package__ in (None, ""):
    current_dir = Path(__file__).resolve().parent
    if str(current_dir) not in sys.path:
        sys.path.insert(0, str(current_dir))

from routers import (
    aggregation_router,
    actor_router,
    behavior_router,
    interaction_router,
    scenario_router,
    simulation_router,
)

app = Agent(
    node_id="simulation-engine",
    agentfield_server=f"{os.getenv('AGENTFIELD_SERVER', 'http://localhost:8080')}",
    ai_config=AIConfig(
        model=os.getenv("AI_MODEL", "openrouter/deepseek/deepseek-v3.1-terminus"),
    ),
)

# Register all routers
for router in (
    scenario_router,
    actor_router,
    behavior_router,
    interaction_router,
    aggregation_router,
    simulation_router,
):
    app.include_router(router)


if __name__ == "__main__":
    print("🎯 Generalized Multi-Agent Simulation System")
    print("🧠 Node ID: simulation-engine")
    print(f"🌐 Control Plane: {app.agentfield_server}")
    print("\n📊 Architecture: Multi-Reasoner Parallel System")
    print("  1. Scenario Analysis → Extract entities, actions, outputs (parallel)")
    print("  2. Actor Generation → Create diverse actor population (parallel)")
    print(
        "  3. Behavior Simulation → Evaluate actions for all actors (massive parallelism)"
    )
    print("  4. Interaction Modeling → Model influence and propagation (parallel)")
    print("  5. Aggregation → Calculate metrics, insights (parallel)")
    print("\n✨ Key Features:")
    print("  - Simple, flat schemas (max 3-4 fields) for all reasoners")
    print("  - Maximum parallelism (100+ concurrent reasoner calls)")
    print("  - Right context to right AI (minimal, focused prompts)")
    print("  - Domain-agnostic (works for any enterprise scenario)")
    print("  - Full observability (reasoning traces for all decisions)")

    port_env = os.getenv("PORT")
    if port_env is None:
        app.run(auto_port=True, host="::")
    else:
        app.run(port=int(port_env), host="::")
