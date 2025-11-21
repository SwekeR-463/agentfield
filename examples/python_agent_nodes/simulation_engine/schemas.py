"""Simple, flat schemas for multi-agent simulation system.

All schemas follow the constraint: maximum 3-4 fields, no nesting, simple types only.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


# ========================= Input Schemas =========================


class SimulationRequest(BaseModel):
    """Main input schema for simulation requests."""

    scenario_description: str = Field(
        description="Natural language description of the scenario"
    )
    scenario_context: str = Field(
        default="{}", description="JSON string with flexible structured data"
    )
    output_requirements: str = Field(
        default="{}", description="JSON string specifying desired outputs"
    )
    max_concurrent: int = Field(
        default=200, description="Maximum number of concurrent reasoner calls"
    )


# ========================= Scenario Analysis Schemas =========================


class EntityExtraction(BaseModel):
    """Simple schema for entity extraction - max 3 fields."""

    entity_type: str = Field(
        description="Type of entity (e.g., 'actor', 'region', 'organization')"
    )
    entity_name: str = Field(description="Name or identifier of the entity")
    description: str = Field(description="Brief description of the entity")


class ActionExtraction(BaseModel):
    """Simple schema for action extraction - max 2 fields."""

    action_name: str = Field(description="Name of the action or decision")
    action_description: str = Field(
        description="Description of what this action entails"
    )


class OutputExtraction(BaseModel):
    """Simple schema for output requirement extraction - max 2 fields."""

    output_name: str = Field(description="Name of the desired output metric or insight")
    output_description: str = Field(
        description="Description of what this output should contain"
    )


# ========================= List Wrapper Schemas (for .ai() calls) =========================


class EntityExtractionList(BaseModel):
    """Wrapper for list of entities - required for Pydantic schema in .ai() calls."""

    entities: list[EntityExtraction] = Field(description="List of extracted entities")


class ActionExtractionList(BaseModel):
    """Wrapper for list of actions - required for Pydantic schema in .ai() calls."""

    actions: list[ActionExtraction] = Field(description="List of extracted actions")


class OutputExtractionList(BaseModel):
    """Wrapper for list of outputs - required for Pydantic schema in .ai() calls."""

    outputs: list[OutputExtraction] = Field(description="List of extracted outputs")


# ========================= Actor Generation Schemas =========================


class ActorTrait(BaseModel):
    """Simple schema for actor trait - max 2 fields."""

    trait_name: str = Field(
        description="Name of the trait (e.g., 'age', 'region', 'preference')"
    )
    trait_value: str = Field(description="Value of the trait")


class ActorAssignment(BaseModel):
    """Simple schema for actor assignment to hierarchy level - max 2 fields."""

    actor_id: str = Field(description="Unique identifier for the actor")
    hierarchy_level: str = Field(
        description="Hierarchy level name (e.g., 'region', 'group')"
    )


# ========================= Behavior Simulation Schemas =========================


class ActionEvaluation(BaseModel):
    """Simple schema for action evaluation - max 2 fields."""

    decision: str = Field(description="The decision or choice made")
    confidence: float = Field(
        description="Confidence score between 0.0 and 1.0", ge=0.0, le=1.0
    )


class Reasoning(BaseModel):
    """Simple schema for reasoning text - max 1 field."""

    reasoning_text: str = Field(
        description="The reasoning or explanation for a decision"
    )


class SentimentScore(BaseModel):
    """Simple schema for sentiment calculation - max 1 field."""

    sentiment_score: float = Field(
        description="Sentiment score between -1.0 and 1.0", ge=-1.0, le=1.0
    )


# ========================= Interaction Schemas =========================


class InfluenceScore(BaseModel):
    """Simple schema for influence modeling - max 2 fields."""

    influence_score: float = Field(
        description="Influence strength between 0.0 and 1.0", ge=0.0, le=1.0
    )
    influence_direction: str = Field(
        description="Direction: 'positive', 'negative', or 'neutral'"
    )


class OpinionUpdate(BaseModel):
    """Simple schema for opinion propagation - max 2 fields."""

    updated_opinion: str = Field(description="The updated opinion after influence")
    change_magnitude: float = Field(
        description="Magnitude of change between 0.0 and 1.0", ge=0.0, le=1.0
    )


# ========================= Aggregation Schemas =========================


class Metric(BaseModel):
    """Simple schema for metric calculation - max 2 fields."""

    metric_name: str = Field(description="Name of the metric")
    metric_value: float = Field(description="Calculated value of the metric")


class LevelAggregation(BaseModel):
    """Simple schema for hierarchy level aggregation - max 2 fields."""

    level_name: str = Field(description="Name of the hierarchy level")
    aggregated_data: str = Field(
        description="JSON string with aggregated data for this level"
    )


class Insight(BaseModel):
    """Simple schema for insight generation - max 1 field."""

    insight_text: str = Field(description="Generated insight or observation")


# ========================= Output Schema =========================


class SimulationResult(BaseModel):
    """Final output schema - uses Dict for flexibility but keeps structure simple."""

    summary: str = Field(description="High-level summary as JSON string")
    statistics: str = Field(description="Statistics as JSON string")
    actor_responses: str = Field(description="Actor responses as JSON string")
    hierarchical_breakdown: str = Field(
        description="Hierarchical breakdown as JSON string"
    )
    reasoning_traces: str = Field(description="Reasoning traces as JSON string")
    recommendations: Optional[str] = Field(
        default=None, description="Recommendations as JSON string if applicable"
    )
