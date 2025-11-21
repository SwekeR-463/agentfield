"""Main simulation orchestrator - coordinates all reasoners with maximum parallelism."""

from __future__ import annotations

import json
import sys
from typing import Dict

from agentfield import AgentRouter
from agentfield.logger import log_info

from schemas import Reasoning, SentimentScore, SimulationRequest, SimulationResult
from utils.parallel_execution import batch_execute, execute_parallel

simulation_router = AgentRouter(tags=["simulation"])


def _get_reasoner(module_name: str, func_name: str):
    """Get reasoner function from module at runtime (after include_router replaces it)."""
    module = sys.modules.get(module_name)
    if module:
        func = getattr(module, func_name, None)
        if func is None:
            raise RuntimeError(
                f"Reasoner {func_name} not found in {module_name}. "
                "Make sure routers are included before calling run_simulation."
            )
        return func
    raise RuntimeError(
        f"Module {module_name} not found. Make sure routers are imported and included."
    )


@simulation_router.reasoner()
async def run_simulation(request: SimulationRequest) -> SimulationResult:
    """
    Main simulation orchestrator.

    Coordinates all reasoners with maximum parallelism, following the pattern:
    1. Analyze scenario (parallel extraction)
    2. Generate actors (parallel trait generation)
    3. Simulate behaviors (massive parallelism: actors × actions)
    4. Aggregate results (parallel metrics and insights)
    """
    log_info(
        f"[run_simulation] Starting simulation: {request.scenario_description[:100]}..."
    )

    # Capture max_concurrent at the start to avoid closure issues
    max_concurrent = request.max_concurrent

    # Step 1: Scenario Analysis (3 parallel calls)
    # Get reasoners at runtime to ensure we get tracked versions
    try:
        extract_entities = _get_reasoner("routers.scenario_router", "extract_entities")
        extract_actions = _get_reasoner("routers.scenario_router", "extract_actions")
        extract_outputs = _get_reasoner("routers.scenario_router", "extract_outputs")
    except Exception as e:
        log_info(f"[run_simulation] Failed to get reasoners: {e}")
        raise

    log_info("[run_simulation] Step 1: Analyzing scenario (parallel extraction)")
    # Capture request values in closure to avoid lambda issues
    scenario_desc = request.scenario_description
    scenario_ctx = request.scenario_context
    output_reqs = request.output_requirements
    max_conc = request.max_concurrent

    entities, actions, outputs = await execute_parallel(
        [
            lambda: extract_entities(scenario_desc, scenario_ctx),
            lambda: extract_actions(scenario_desc, scenario_ctx),
            lambda: extract_outputs(scenario_desc, output_reqs),
        ],
        max_concurrent=max_conc,
    )

    # Handle exceptions
    if isinstance(entities, Exception):
        log_info("[run_simulation] Warning: entities extraction failed")
        entities = []
    if isinstance(actions, Exception):
        log_info("[run_simulation] Warning: actions extraction failed")
        actions = []
    if isinstance(outputs, Exception):
        log_info("[run_simulation] Warning: outputs extraction failed")
        outputs = []

    log_info(
        f"[run_simulation] Extracted {len(entities)} entities, {len(actions)} actions, {len(outputs)} outputs"
    )

    # Step 2: Generate Actor Population (MAXIMUM PARALLELISM)
    # Create actors based on entities of type 'actor' or generate default population
    actor_entities = [
        e
        for e in entities
        if e.entity_type.lower() in ["actor", "customer", "person", "user"]
    ]
    # Scale up: default to 50 actors for large-scale simulation (configurable via scenario_context)
    try:
        context_dict = (
            json.loads(request.scenario_context) if request.scenario_context else {}
        )
        num_actors = context_dict.get("num_actors", max(len(actor_entities), 50))
    except Exception:
        num_actors = max(len(actor_entities), 50)

    log_info(
        f"[run_simulation] Step 2: Generating {num_actors} actors with traits (MASSIVE PARALLELISM)"
    )

    # Generate actor IDs
    actor_ids = [f"actor_{i:04d}" for i in range(num_actors)]

    # Generate ALL traits in parallel (not per-actor sequentially)
    # Each actor gets 3 traits, so we generate num_actors * 3 traits in parallel
    trait_types = ["demographic", "preference", "behavior"]
    actor_traits_map: Dict[str, Dict[str, str]] = {}

    # Create all trait generation tasks
    trait_tasks = []
    for actor_id in actor_ids:
        for trait_type in trait_types:
            trait_tasks.append((actor_id, trait_type))

    log_info(f"[run_simulation] Generating {len(trait_tasks)} traits in parallel")

    # Get reasoner at runtime
    try:
        generate_actor_trait = _get_reasoner(
            "routers.actor_router", "generate_actor_trait"
        )
    except Exception as e:
        log_info(f"[run_simulation] Failed to get generate_actor_trait: {e}")
        raise

    # Capture request values for closure
    scenario_desc = request.scenario_description

    async def generate_single_trait(task_tuple):
        """Generate one trait for one actor - fully parallelized."""
        actor_id, trait_type = task_tuple
        trait = await generate_actor_trait(
            actor_id=actor_id,
            scenario_description=scenario_desc,
            trait_type=trait_type,
            existing_traits="{}",
        )
        return actor_id, trait.trait_name, trait.trait_value

    # Generate ALL traits in one massive parallel batch
    trait_results = await batch_execute(
        trait_tasks,
        generate_single_trait,
        batch_size=max_concurrent,
        max_concurrent=max_concurrent,
    )

    # Aggregate traits by actor
    for result in trait_results:
        if isinstance(result, Exception):
            continue
        try:
            actor_id, trait_name, trait_value = result
            if actor_id not in actor_traits_map:
                actor_traits_map[actor_id] = {}
            actor_traits_map[actor_id][trait_name] = trait_value
        except (ValueError, TypeError):
            log_info(
                f"[run_simulation] Warning: Failed to unpack trait result: {result}"
            )

    log_info(
        f"[run_simulation] Generated traits for {len(actor_traits_map)} actors ({len(trait_tasks)} traits total)"
    )

    # Assign actors to hierarchy levels (parallel)
    hierarchy_level_names = [
        e.entity_name
        for e in entities
        if e.entity_type.lower() in ["region", "group", "organization", "level"]
    ]
    if not hierarchy_level_names:
        hierarchy_level_names = ["default"]
    hierarchy_levels_json = json.dumps(hierarchy_level_names)

    # Get reasoner at runtime
    assign_actor_to_group = _get_reasoner(
        "routers.actor_router", "assign_actor_to_group"
    )

    async def assign_actor(actor_id: str):
        """Assign one actor to a hierarchy level."""
        return await assign_actor_to_group(
            actor_id=actor_id,
            scenario_description=request.scenario_description,
            hierarchy_levels=hierarchy_levels_json,
        )

    assignments = await batch_execute(
        list(actor_traits_map.keys()),
        assign_actor,
        batch_size=max_concurrent,
        max_concurrent=max_concurrent,
    )
    actor_assignments: Dict[str, str] = {}
    for assignment in assignments:
        if isinstance(assignment, Exception):
            continue
        if hasattr(assignment, "actor_id"):
            actor_assignments[assignment.actor_id] = assignment.hierarchy_level

    log_info(
        f"[run_simulation] Assigned {len(actor_assignments)} actors to hierarchy levels"
    )

    # Step 3: Behavior Simulation (Massive Parallelism)
    log_info("[run_simulation] Step 3: Simulating behaviors (massive parallelism)")

    # For each (actor, action) combination, evaluate the action
    actor_responses: list[Dict] = []

    # Get reasoner at runtime
    try:
        evaluate_action = _get_reasoner("routers.behavior_router", "evaluate_action")
    except Exception as e:
        log_info(f"[run_simulation] Failed to get evaluate_action: {e}")
        raise

    # Capture request values for closure
    scenario_ctx = request.scenario_context

    async def evaluate_actor_action(actor_id: str, action: str):
        """Evaluate one action for one actor."""
        actor_traits_json = json.dumps(actor_traits_map.get(actor_id, {}))
        evaluation = await evaluate_action(
            actor_id=actor_id,
            action_description=action,
            actor_traits=actor_traits_json,
            scenario_context=scenario_ctx,
        )
        return actor_id, action, evaluation

    # Create all (actor, action) combinations
    action_descriptions = (
        [a.action_description for a in actions] if actions else ["evaluate scenario"]
    )
    evaluation_tasks = []
    for actor_id in actor_traits_map.keys():
        for action_desc in action_descriptions:
            evaluation_tasks.append((actor_id, action_desc))

    log_info(
        f"[run_simulation] Evaluating {len(evaluation_tasks)} actor-action combinations in parallel"
    )

    # Execute evaluations in parallel batches
    async def evaluate_task(task_tuple):
        """Wrapper to unpack tuple for batch_execute."""
        actor_id, action_desc = task_tuple
        return await evaluate_actor_action(actor_id, action_desc)

    evaluation_results = await batch_execute(
        evaluation_tasks,
        evaluate_task,
        batch_size=max_concurrent,
        max_concurrent=max_concurrent,
    )

    log_info(
        f"[run_simulation] Completed {len(evaluation_results)} evaluations, now generating reasoning/sentiment in parallel"
    )

    # Collect all valid evaluations for batch processing
    valid_evaluations = []
    for result in evaluation_results:
        if isinstance(result, Exception):
            continue
        try:
            actor_id, action_desc, evaluation = result
            if isinstance(evaluation, Exception) or not hasattr(evaluation, "decision"):
                continue
            valid_evaluations.append((actor_id, action_desc, evaluation))
        except (ValueError, TypeError):
            continue

    log_info(f"[run_simulation] Processing {len(valid_evaluations)} valid evaluations")

    # Generate ALL reasoning and sentiment in parallel (not one-by-one!)
    # Create task data with proper indexing
    reasoning_task_data = []
    sentiment_task_data = []

    for idx, (actor_id, action_desc, evaluation) in enumerate(valid_evaluations):
        actor_traits_json = json.dumps(actor_traits_map.get(actor_id, {}))
        reasoning_task_data.append(
            (idx, actor_id, evaluation.decision, actor_traits_json)
        )
        sentiment_task_data.append((idx, evaluation.decision))

    log_info(
        f"[run_simulation] Generating {len(reasoning_task_data)} reasoning and {len(sentiment_task_data)} sentiment in parallel"
    )

    # Get reasoners at runtime
    try:
        generate_reasoning = _get_reasoner(
            "routers.behavior_router", "generate_reasoning"
        )
        calculate_sentiment = _get_reasoner(
            "routers.behavior_router", "calculate_sentiment"
        )
    except Exception as e:
        log_info(f"[run_simulation] Failed to get behavior reasoners: {e}")
        raise

    async def generate_reasoning_task(data_tuple):
        """Generate reasoning for one evaluation."""
        eval_idx, actor_id, decision, traits_json = data_tuple
        result = await generate_reasoning(
            actor_id=actor_id,
            decision=decision,
            actor_traits=traits_json,
        )
        return ("reasoning", eval_idx, result)

    async def generate_sentiment_task(data_tuple):
        """Generate sentiment for one evaluation."""
        eval_idx, decision = data_tuple
        result = await calculate_sentiment(text=decision)
        return ("sentiment", eval_idx, result)

    # Execute ALL reasoning and sentiment in parallel using batch_execute
    reasoning_results_dict: Dict[int, Reasoning] = {}
    sentiment_results_dict: Dict[int, SentimentScore] = {}

    # Execute reasoning tasks
    reasoning_results = await batch_execute(
        reasoning_task_data,
        generate_reasoning_task,
        batch_size=max_concurrent,
        max_concurrent=max_concurrent,
    )

    # Execute sentiment tasks
    sentiment_results = await batch_execute(
        sentiment_task_data,
        generate_sentiment_task,
        batch_size=max_concurrent,
        max_concurrent=max_concurrent,
    )

    # Combine results
    all_results = list(reasoning_results) + list(sentiment_results)

    # Parse results
    for result in all_results:
        if isinstance(result, Exception):
            continue
        try:
            task_type, eval_idx, task_result = result
            if task_type == "reasoning":
                reasoning_results_dict[eval_idx] = task_result
            elif task_type == "sentiment":
                sentiment_results_dict[eval_idx] = task_result
        except (ValueError, TypeError) as e:
            log_info(f"[run_simulation] Warning: Failed to parse result: {e}")
            continue

    # Build actor responses
    for idx, (actor_id, action_desc, evaluation) in enumerate(valid_evaluations):
        reasoning = reasoning_results_dict.get(idx)
        sentiment = sentiment_results_dict.get(idx)

        actor_response = {
            "actor_id": actor_id,
            "action": action_desc,
            "decision": evaluation.decision,
            "confidence": evaluation.confidence,
            "reasoning": (
                reasoning.reasoning_text if isinstance(reasoning, Reasoning) else ""
            ),
            "sentiment": (
                sentiment.sentiment_score
                if isinstance(sentiment, SentimentScore)
                else 0.0
            ),
            "hierarchy_level": actor_assignments.get(actor_id, "default"),
        }
        actor_responses.append(actor_response)

    log_info(f"[run_simulation] Generated {len(actor_responses)} actor responses")

    # Step 4: Aggregation (Parallel Metrics and Insights)
    log_info(
        "[run_simulation] Step 4: Aggregating results (parallel metrics and insights)"
    )

    # Calculate metrics in parallel
    actor_responses_json = json.dumps(actor_responses)
    metrics: list[Dict] = []

    # Get reasoner at runtime
    try:
        calculate_metric = _get_reasoner(
            "routers.aggregation_router", "calculate_metric"
        )
    except Exception as e:
        log_info(f"[run_simulation] Failed to get calculate_metric: {e}")
        raise

    async def calculate_one_metric(output: str):
        """Calculate one metric."""
        return await calculate_metric(
            metric_name=output,
            metric_description=f"Calculate {output} from simulation results",
            data_json=actor_responses_json,
        )

    output_names = (
        [o.output_name for o in outputs]
        if outputs
        else ["positive_rate", "average_sentiment"]
    )
    metric_results = await batch_execute(
        output_names,
        calculate_one_metric,
        batch_size=max_concurrent,
        max_concurrent=max_concurrent,
    )

    for metric_result in metric_results:
        if isinstance(metric_result, Exception):
            continue
        if hasattr(metric_result, "metric_name"):
            metrics.append(
                {"name": metric_result.metric_name, "value": metric_result.metric_value}
            )

    log_info(f"[run_simulation] Calculated {len(metrics)} metrics")

    # Aggregate by hierarchy level (parallel)
    level_aggregations: Dict[str, Dict] = {}
    unique_levels = set(actor_assignments.values())

    # Get reasoner at runtime
    aggregate_by_level = _get_reasoner(
        "routers.aggregation_router", "aggregate_by_level"
    )

    async def aggregate_one_level(level_name: str):
        """Aggregate one hierarchy level."""
        level_actors = [
            r for r in actor_responses if r.get("hierarchy_level") == level_name
        ]
        level_data_json = json.dumps(level_actors)
        return await aggregate_by_level(
            level_name=level_name,
            level_description=f"Aggregate results for {level_name}",
            actor_data_json=level_data_json,
        )

    aggregation_results = await batch_execute(
        list(unique_levels),
        aggregate_one_level,
        batch_size=max_concurrent,
        max_concurrent=max_concurrent,
    )

    for agg_result in aggregation_results:
        if isinstance(agg_result, Exception):
            continue
        if hasattr(agg_result, "level_name"):
            try:
                level_aggregations[agg_result.level_name] = json.loads(
                    agg_result.aggregated_data
                )
            except Exception:
                level_aggregations[agg_result.level_name] = {}

    log_info(f"[run_simulation] Aggregated {len(level_aggregations)} hierarchy levels")

    # Generate insights (parallel)
    insights: list[str] = []
    insight_types = ["key_findings", "recommendations", "concerns", "opportunities"]

    # Get reasoner at runtime
    try:
        generate_insight = _get_reasoner(
            "routers.aggregation_router", "generate_insight"
        )
    except Exception as e:
        log_info(f"[run_simulation] Failed to get generate_insight: {e}")
        raise

    async def generate_one_insight(insight_type: str):
        """Generate one insight."""
        return await generate_insight(
            insight_type=insight_type,
            data_json=actor_responses_json,
            scenario_description=request.scenario_description,
        )

    insight_results = await batch_execute(
        insight_types,
        generate_one_insight,
        batch_size=max_concurrent,
        max_concurrent=max_concurrent,
    )

    for insight_result in insight_results:
        if isinstance(insight_result, Exception):
            continue
        if hasattr(insight_result, "insight_text"):
            insights.append(insight_result.insight_text)

    log_info(f"[run_simulation] Generated {len(insights)} insights")

    # Step 5: Compile Final Results
    log_info("[run_simulation] Step 5: Compiling final results")

    summary = {
        "total_actors": len(actor_traits_map),
        "total_actions": len(action_descriptions),
        "total_responses": len(actor_responses),
        "hierarchy_levels": list(unique_levels),
    }

    statistics = {m["name"]: m["value"] for m in metrics}

    recommendations = None
    if outputs and "recommendations" in [o.output_name for o in outputs]:
        recommendations = {"insights": insights[:3]}

    result = SimulationResult(
        summary=json.dumps(summary),
        statistics=json.dumps(statistics),
        actor_responses=json.dumps(actor_responses),
        hierarchical_breakdown=json.dumps(level_aggregations),
        reasoning_traces=json.dumps(
            actor_responses
        ),  # Full traces included in actor_responses
        recommendations=json.dumps(recommendations) if recommendations else None,
    )

    log_info("[run_simulation] Simulation completed successfully")
    return result
