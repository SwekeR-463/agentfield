"""Interaction modeling reasoners - model influence and opinion propagation."""

from __future__ import annotations

from agentfield import AgentRouter

from schemas import InfluenceScore, OpinionUpdate

interaction_router = AgentRouter(tags=["interaction"])


@interaction_router.reasoner()
async def model_influence(
    influencer_id: str,
    influencee_id: str,
    influencer_opinion: str,
    influencee_traits: str,
) -> InfluenceScore:
    """
    Model how one actor influences another.

    This reasoner calculates the strength and direction of influence between two actors.
    Can run in parallel for many actor pairs.
    """
    system_prompt = (
        "You are modeling social influence between actors in a simulation. "
        "Your task is to determine how strongly one actor influences another.\n\n"
        "Consider:\n"
        "- The relationship between the actors\n"
        "- The influencer's opinion or decision\n"
        "- The influencee's characteristics\n"
        "- Realistic social dynamics\n\n"
        "Return an influence score with:\n"
        "- influence_score: Strength between 0.0 (no influence) and 1.0 (strong influence)\n"
        "- influence_direction: 'positive', 'negative', or 'neutral'\n\n"
        "Be realistic about influence strength. Not all interactions are equally influential."
    )

    user_prompt = (
        f"Influencer ID: {influencer_id}\n"
        f"Influencer's Opinion: {influencer_opinion}\n"
        f"Influencee ID: {influencee_id}\n"
        f"Influencee Traits (JSON): {influencee_traits}\n\n"
        "How strongly does the influencer influence the influencee, and in what direction?"
    )

    response = await interaction_router.ai(
        system=system_prompt,
        user=user_prompt,
        schema=InfluenceScore,
    )

    if isinstance(response, InfluenceScore):
        return response
    return InfluenceScore(influence_score=0.0, influence_direction="neutral")


@interaction_router.reasoner()
async def propagate_opinion(
    actor_id: str,
    current_opinion: str,
    influence_scores: str,
    influencer_opinions: str,
) -> OpinionUpdate:
    """
    Propagate opinions through influence network.

    This reasoner updates an actor's opinion based on influences from other actors.
    Can run in parallel for many actors.
    """
    system_prompt = (
        "You are modeling how opinions change through social influence. "
        "Your task is to determine how an actor's opinion updates based on influences from others.\n\n"
        "Consider:\n"
        "- The actor's current opinion\n"
        "- The strength of various influences\n"
        "- The opinions of influencers\n"
        "- Realistic opinion change dynamics\n\n"
        "Return an opinion update with:\n"
        "- updated_opinion: The new opinion after considering influences\n"
        "- change_magnitude: How much the opinion changed (0.0 to 1.0)\n\n"
        "Be realistic. Opinions don't always change dramatically."
    )

    user_prompt = (
        f"Actor ID: {actor_id}\n"
        f"Current Opinion: {current_opinion}\n"
        f"Influence Scores (JSON): {influence_scores}\n"
        f"Influencer Opinions (JSON): {influencer_opinions}\n\n"
        "How does this actor's opinion update after considering these influences?"
    )

    response = await interaction_router.ai(
        system=system_prompt,
        user=user_prompt,
        schema=OpinionUpdate,
    )

    if isinstance(response, OpinionUpdate):
        return response
    return OpinionUpdate(updated_opinion=current_opinion, change_magnitude=0.0)
