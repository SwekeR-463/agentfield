"""Example: Pricing Disruption Scenario

This example demonstrates how to use the simulation engine to simulate
customer reactions to different discount levels across regions.
"""

import asyncio
import json

from schemas import SimulationRequest


async def run_pricing_disruption_example():
    """Run a pricing disruption simulation example."""

    # Define the scenario
    request = SimulationRequest(
        scenario_description=(
            "A company is experiencing supply chain delays and needs to decide on discount levels. "
            "They want to understand how customers in North America, Europe, and Asia would react "
            "to discounts of 5%, 10%, 15%, or 20%. The company needs to balance customer satisfaction "
            "with profitability."
        ),
        scenario_context=json.dumps(
            {
                "company": "TechCorp",
                "product": "Premium Laptop",
                "regions": ["North America", "Europe", "Asia"],
                "discount_options": [5, 10, 15, 20],
                "base_price": 1000,
                "supply_chain_delay_days": 30,
            }
        ),
        output_requirements=json.dumps(
            {
                "include_recommendations": True,
                "breakdown_by_region": True,
                "include_sentiment_analysis": True,
                "include_purchase_intent": True,
                "compare_discount_options": True,
            }
        ),
    )

    print("🎯 Running Pricing Disruption Simulation")
    print(f"Scenario: {request.scenario_description[:100]}...")
    print("\nThis simulation will:")
    print("  1. Extract entities (customers, regions, company)")
    print("  2. Extract actions (evaluate discount options)")
    print("  3. Generate diverse customer actors (parallel)")
    print(
        "  4. Evaluate each customer's reaction to each discount (massive parallelism)"
    )
    print("  5. Aggregate results by region")
    print("  6. Generate recommendations")
    print("\n⏳ Running simulation...\n")

    # In a real scenario, you would call the simulation via HTTP:
    # import httpx
    # response = await httpx.post(
    #     "http://localhost:8000/reasoners/run_simulation",
    #     json=request.model_dump()
    # )
    # result = response.json()

    # For this example, we'll just show the request structure
    print("Request Structure:")
    print(json.dumps(request.model_dump(), indent=2))
    print("\n✅ Example request prepared!")
    print("\nTo run this simulation:")
    print("  1. Start the simulation engine: python main.py")
    print("  2. POST to /reasoners/run_simulation with the request above")
    print("  3. Receive SimulationResult with aggregated insights")


if __name__ == "__main__":
    asyncio.run(run_pricing_disruption_example())
