"""Aggregation reasoners - calculate metrics, aggregate by level, generate insights."""

from __future__ import annotations


from agentfield import AgentRouter

from schemas import Insight, LevelAggregation, Metric

aggregation_router = AgentRouter(tags=["aggregation"])


@aggregation_router.reasoner()
async def calculate_metric(
    metric_name: str, metric_description: str, data_json: str
) -> Metric:
    """
    Calculate a single metric from data.

    This reasoner calculates one metric. Can run in parallel for many metrics.
    Each call gets minimal context: just the metric name, description, and data.
    """
    system_prompt = (
        "You are an expert at calculating metrics from simulation data. "
        "Your task is to calculate a specific metric from the provided data.\n\n"
        "Analyze the data carefully and calculate the metric accurately. "
        "Return a metric with:\n"
        "- metric_name: The name of the metric\n"
        "- metric_value: The calculated value (as a float)\n\n"
        "Be precise and accurate in your calculation."
    )

    user_prompt = (
        f"Metric Name: {metric_name}\n"
        f"Metric Description: {metric_description}\n"
        f"Data (JSON): {data_json}\n\n"
        f"Calculate the {metric_name} metric from this data."
    )

    response = await aggregation_router.ai(
        system=system_prompt,
        user=user_prompt,
        schema=Metric,
    )

    if isinstance(response, Metric):
        return response
    return Metric(metric_name=metric_name, metric_value=0.0)


@aggregation_router.reasoner()
async def aggregate_by_level(
    level_name: str, level_description: str, actor_data_json: str
) -> LevelAggregation:
    """
    Aggregate simulation results by hierarchy level.

    This reasoner aggregates data for one hierarchy level (e.g., one region).
    Can run in parallel for many levels.
    """
    system_prompt = (
        "You are an expert at aggregating simulation results by hierarchy level. "
        "Your task is to aggregate actor data for a specific hierarchy level.\n\n"
        "Analyze all actors at this level and create aggregated statistics, summaries, "
        "and insights. Return the aggregated data as a JSON string.\n\n"
        "The aggregated data should include:\n"
        "- Summary statistics (counts, averages, distributions)\n"
        "- Key patterns or trends\n"
        "- Representative examples\n"
        "- Any level-specific insights\n\n"
        "Return an aggregation with:\n"
        "- level_name: The name of the hierarchy level\n"
        "- aggregated_data: JSON string with aggregated results\n\n"
        "Be thorough but concise. Create meaningful aggregations."
    )

    user_prompt = (
        f"Hierarchy Level: {level_name}\n"
        f"Level Description: {level_description}\n"
        f"Actor Data for this Level (JSON): {actor_data_json}\n\n"
        f"Aggregate all data for the {level_name} level."
    )

    response = await aggregation_router.ai(
        system=system_prompt,
        user=user_prompt,
        schema=LevelAggregation,
    )

    if isinstance(response, LevelAggregation):
        return response
    return LevelAggregation(level_name=level_name, aggregated_data="{}")


@aggregation_router.reasoner()
async def generate_insight(
    insight_type: str, data_json: str, scenario_description: str
) -> Insight:
    """
    Generate a single insight from simulation data.

    This reasoner generates one insight. Can run in parallel for many insights.
    Each call gets minimal context.
    """
    system_prompt = (
        "You are an expert at generating insights from simulation data. "
        "Your task is to generate a specific type of insight.\n\n"
        "Insights should be:\n"
        "- Actionable and relevant\n"
        "- Based on the data provided\n"
        "- Clear and concise (1-3 sentences)\n"
        "- Specific to the scenario\n\n"
        "Return an insight with:\n"
        "- insight_text: The generated insight\n\n"
        "Be insightful and useful. Avoid generic statements."
    )

    user_prompt = (
        f"Insight Type: {insight_type}\n"
        f"Scenario: {scenario_description}\n"
        f"Data (JSON): {data_json}\n\n"
        f"Generate a {insight_type} insight from this data."
    )

    response = await aggregation_router.ai(
        system=system_prompt,
        user=user_prompt,
        schema=Insight,
    )

    if isinstance(response, Insight):
        return response
    return Insight(insight_text="No insight generated")
