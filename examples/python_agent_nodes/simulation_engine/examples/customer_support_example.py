"""Example: Customer Support Routing Scenario

This example demonstrates how to use the simulation engine to simulate
different support ticket routing strategies and their impact on satisfaction.
"""

import asyncio
import json

from schemas import SimulationRequest


async def run_customer_support_example():
    """Run a customer support routing simulation example."""

    # Define the scenario
    request = SimulationRequest(
        scenario_description=(
            "A SaaS company wants to simulate how different support ticket routing strategies "
            "affect customer satisfaction. They have 3 routing options: round-robin, skill-based, "
            "and priority-based. The company needs to understand which strategy maximizes "
            "customer satisfaction while maintaining efficient resolution times."
        ),
        scenario_context=json.dumps(
            {
                "company": "SaaS Corp",
                "ticket_volume": 1000,
                "support_agents": 20,
                "routing_strategies": ["round-robin", "skill-based", "priority-based"],
                "average_resolution_time_hours": 4,
                "customer_segments": ["enterprise", "small_business", "individual"],
            }
        ),
        output_requirements=json.dumps(
            {
                "include_satisfaction_metrics": True,
                "compare_strategies": True,
                "include_resolution_times": True,
                "breakdown_by_segment": True,
                "include_recommendations": True,
            }
        ),
    )

    print("🎯 Running Customer Support Routing Simulation")
    print(f"Scenario: {request.scenario_description[:100]}...")
    print("\nThis simulation will:")
    print("  1. Extract entities (customers, support agents, routing strategies)")
    print("  2. Extract actions (ticket creation, routing decisions, resolution)")
    print("  3. Generate diverse customer and agent actors (parallel)")
    print("  4. Simulate ticket flow through each routing strategy (parallel)")
    print("  5. Calculate satisfaction metrics for each strategy")
    print("  6. Generate comparison insights and recommendations")
    print("\n⏳ Running simulation...\n")

    print("Request Structure:")
    print(json.dumps(request.model_dump(), indent=2))
    print("\n✅ Example request prepared!")
    print("\nTo run this simulation:")
    print("  1. Start the simulation engine: python main.py")
    print("  2. POST to /reasoners/run_simulation with the request above")
    print("  3. Receive SimulationResult comparing routing strategies")


if __name__ == "__main__":
    asyncio.run(run_customer_support_example())
