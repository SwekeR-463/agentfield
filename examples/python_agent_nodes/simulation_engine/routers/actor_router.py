"""Actor generation reasoners - create actor traits and assignments."""

from __future__ import annotations

from agentfield import AgentRouter

from schemas import ActorAssignment, ActorTrait

actor_router = AgentRouter(tags=["actor"])


@actor_router.reasoner()
async def generate_actor_trait(
    actor_id: str,
    scenario_description: str,
    trait_type: str,
    existing_traits: str = "{}",
) -> ActorTrait:
    """
    Generate a single trait for an actor.

    This reasoner is designed to be called many times in parallel for different actors.
    Each call generates one trait with minimal context.
    """
    system_prompt = (
        "You are an expert at creating realistic actor characteristics for simulations. "
        "Your task is to generate a single trait for an actor based on the scenario.\n\n"
        "Generate diverse, realistic traits that reflect real-world variation. "
        "The trait should be relevant to the scenario and help the actor make decisions.\n\n"
        "Return a trait with:\n"
        "- trait_name: The name of the trait (e.g., 'age', 'region', 'preference', 'budget')\n"
        "- trait_value: The value of this trait\n\n"
        "Be specific and realistic. Avoid generic values."
    )

    user_prompt = (
        f"Actor ID: {actor_id}\n"
        f"Trait Type: {trait_type}\n"
        f"Scenario: {scenario_description}\n"
        f"Existing Traits (JSON): {existing_traits}\n\n"
        f"Generate a {trait_type} trait for this actor. Make it diverse and realistic."
    )

    response = await actor_router.ai(
        system=system_prompt,
        user=user_prompt,
        schema=ActorTrait,
    )

    if isinstance(response, ActorTrait):
        return response
    return ActorTrait(trait_name=trait_type, trait_value="unknown")


@actor_router.reasoner()
async def assign_actor_to_group(
    actor_id: str, scenario_description: str, hierarchy_levels: str
) -> ActorAssignment:
    """
    Assign an actor to a hierarchy level (region, group, etc.).

    This reasoner assigns actors to groups based on their traits and scenario context.
    """
    system_prompt = (
        "You are an expert at organizing actors into hierarchical groups. "
        "Your task is to assign an actor to an appropriate hierarchy level based on the scenario.\n\n"
        "Return an assignment with:\n"
        "- actor_id: The actor identifier\n"
        "- hierarchy_level: The name of the hierarchy level this actor belongs to\n\n"
        "Make assignments that are logical and realistic for the scenario."
    )

    user_prompt = (
        f"Actor ID: {actor_id}\n"
        f"Scenario: {scenario_description}\n"
        f"Available Hierarchy Levels (JSON): {hierarchy_levels}\n\n"
        "Assign this actor to an appropriate hierarchy level."
    )

    response = await actor_router.ai(
        system=system_prompt,
        user=user_prompt,
        schema=ActorAssignment,
    )

    if isinstance(response, ActorAssignment):
        return response
    return ActorAssignment(actor_id=actor_id, hierarchy_level="default")
