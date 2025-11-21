"""Scenario analysis reasoners - extract entities, actions, and outputs."""

from __future__ import annotations

from agentfield import AgentRouter

from schemas import (
    ActionExtraction,
    ActionExtractionList,
    EntityExtraction,
    EntityExtractionList,
    OutputExtraction,
    OutputExtractionList,
)

scenario_router = AgentRouter(tags=["scenario"])


@scenario_router.reasoner()
async def extract_entities(
    scenario_description: str, scenario_context: str
) -> list[EntityExtraction]:
    """
    Extract entities from scenario description.

    Returns a list of entities (actors, organizations, regions, etc.) with simple schema.
    """
    system_prompt = (
        "You are an expert at analyzing business scenarios and extracting key entities. "
        "Your task is to identify all entities mentioned in the scenario description. "
        "Entities can be: actors (people, customers, employees), organizations, regions, "
        "products, services, or any other relevant entities.\n\n"
        "Return a list of entities. Each entity should have:\n"
        "- entity_type: The type (e.g., 'actor', 'region', 'organization')\n"
        "- entity_name: The name or identifier\n"
        "- description: A brief description\n\n"
        "Be thorough but concise. Extract 5-15 entities depending on scenario complexity."
    )

    user_prompt = (
        f"Scenario Description:\n{scenario_description}\n\n"
        f"Scenario Context (JSON):\n{scenario_context}\n\n"
        "Extract all entities from this scenario."
    )

    response = await scenario_router.ai(
        system=system_prompt,
        user=user_prompt,
        schema=EntityExtractionList,
    )

    if isinstance(response, EntityExtractionList):
        return response.entities
    return []


@scenario_router.reasoner()
async def extract_actions(
    scenario_description: str, scenario_context: str
) -> list[ActionExtraction]:
    """
    Extract possible actions or decisions from scenario description.

    Returns a list of actions with simple schema.
    """
    system_prompt = (
        "You are an expert at analyzing business scenarios and extracting possible actions or decisions. "
        "Your task is to identify all actions that actors might take or decisions they might make.\n\n"
        "Actions can be: purchase decisions, support interactions, policy choices, "
        "routing decisions, or any other behaviors relevant to the scenario.\n\n"
        "Return a list of actions. Each action should have:\n"
        "- action_name: The name of the action\n"
        "- action_description: What this action entails\n\n"
        "Extract 3-10 actions depending on scenario complexity."
    )

    user_prompt = (
        f"Scenario Description:\n{scenario_description}\n\n"
        f"Scenario Context (JSON):\n{scenario_context}\n\n"
        "Extract all possible actions or decisions from this scenario."
    )

    response = await scenario_router.ai(
        system=system_prompt,
        user=user_prompt,
        schema=ActionExtractionList,
    )

    if isinstance(response, ActionExtractionList):
        return response.actions
    return []


@scenario_router.reasoner()
async def extract_outputs(
    scenario_description: str, output_requirements: str
) -> list[OutputExtraction]:
    """
    Extract desired output requirements from scenario description.

    Returns a list of output requirements with simple schema.
    """
    system_prompt = (
        "You are an expert at analyzing business scenarios and extracting output requirements. "
        "Your task is to identify what outputs, metrics, or insights are needed from the simulation.\n\n"
        "Outputs can be: statistics, recommendations, sentiment analysis, breakdowns by region, "
        "or any other metrics or insights relevant to the scenario.\n\n"
        "Return a list of outputs. Each output should have:\n"
        "- output_name: The name of the output\n"
        "- output_description: What this output should contain\n\n"
        "Extract 3-8 outputs depending on requirements."
    )

    user_prompt = (
        f"Scenario Description:\n{scenario_description}\n\n"
        f"Output Requirements (JSON):\n{output_requirements}\n\n"
        "Extract all desired outputs from this scenario."
    )

    response = await scenario_router.ai(
        system=system_prompt,
        user=user_prompt,
        schema=OutputExtractionList,
    )

    if isinstance(response, OutputExtractionList):
        return response.outputs
    return []
