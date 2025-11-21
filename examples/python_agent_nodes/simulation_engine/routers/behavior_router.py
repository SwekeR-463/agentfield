"""Behavior simulation reasoners - evaluate actions, generate reasoning, calculate sentiment."""

from __future__ import annotations

from agentfield import AgentRouter

from schemas import ActionEvaluation, Reasoning, SentimentScore

behavior_router = AgentRouter(tags=["behavior"])


@behavior_router.reasoner()
async def evaluate_action(
    actor_id: str,
    action_description: str,
    actor_traits: str,
    scenario_context: str,
) -> ActionEvaluation:
    """
    Evaluate an action from an actor's perspective.

    This is the core decision-making reasoner. It's designed to be called many times
    in parallel for different (actor, action) combinations.
    Each call gets minimal, focused context.
    """
    system_prompt = (
        "You are simulating how a real person would evaluate and decide on an action. "
        "Your task is to make a decision based on the actor's characteristics and the scenario context.\n\n"
        "Think like the actor would think. Consider their traits, preferences, and situation. "
        "Make a realistic decision that reflects how this type of person would actually behave.\n\n"
        "Return an evaluation with:\n"
        "- decision: The decision or choice made (be specific)\n"
        "- confidence: A confidence score between 0.0 and 1.0\n\n"
        "Be realistic and nuanced. Not everyone makes the same decision."
    )

    user_prompt = (
        f"Actor ID: {actor_id}\n"
        f"Actor Traits (JSON): {actor_traits}\n"
        f"Action to Evaluate: {action_description}\n"
        f"Scenario Context (JSON): {scenario_context}\n\n"
        "How would this actor evaluate and decide on this action?"
    )

    response = await behavior_router.ai(
        system=system_prompt,
        user=user_prompt,
        schema=ActionEvaluation,
    )

    if isinstance(response, ActionEvaluation):
        return response
    return ActionEvaluation(decision="unknown", confidence=0.5)


@behavior_router.reasoner()
async def generate_reasoning(
    actor_id: str, decision: str, actor_traits: str
) -> Reasoning:
    """
    Generate reasoning text for a decision.

    This reasoner explains why an actor made a particular decision.
    Called after evaluate_action, can run in parallel for many actors.
    """
    system_prompt = (
        "You are explaining the reasoning behind an actor's decision. "
        "Your task is to generate a clear, realistic explanation of why this decision was made.\n\n"
        "The reasoning should:\n"
        "- Reflect the actor's traits and characteristics\n"
        "- Be realistic and human-like\n"
        "- Be specific to this decision\n"
        "- Be 2-4 sentences long\n\n"
        "Return reasoning text that explains the decision."
    )

    user_prompt = (
        f"Actor ID: {actor_id}\n"
        f"Decision Made: {decision}\n"
        f"Actor Traits (JSON): {actor_traits}\n\n"
        "Explain why this actor made this decision."
    )

    response = await behavior_router.ai(
        system=system_prompt,
        user=user_prompt,
        schema=Reasoning,
    )

    if isinstance(response, Reasoning):
        return response
    return Reasoning(reasoning_text="No reasoning provided")


@behavior_router.reasoner()
async def calculate_sentiment(text: str) -> SentimentScore:
    """
    Calculate sentiment score from text.

    This reasoner analyzes sentiment of reasoning text or other actor outputs.
    Can run in parallel for many texts.
    """
    system_prompt = (
        "You are a sentiment analysis expert. "
        "Your task is to calculate a sentiment score for the given text.\n\n"
        "Return a sentiment score between -1.0 (very negative) and 1.0 (very positive).\n"
        "0.0 is neutral.\n\n"
        "Be accurate and nuanced. Consider context and tone."
    )

    user_prompt = f"Text to analyze:\n{text}\n\nCalculate the sentiment score."

    response = await behavior_router.ai(
        system=system_prompt,
        user=user_prompt,
        schema=SentimentScore,
    )

    if isinstance(response, SentimentScore):
        return response
    return SentimentScore(sentiment_score=0.0)
