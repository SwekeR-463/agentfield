"""Recursive planning router for deep research agent."""

from __future__ import annotations

import asyncio
from typing import List

from agentfield import AgentRouter

from schemas import (
    ResearchPlan,
    Subtask,
    TaskDescriptions,
    TaskDependenciesList,
)


planning_router = AgentRouter(prefix="planning")


def _build_topological_groups(tasks: List[Subtask]) -> List[List[str]]:
    """
    Build topological groups using topological sort.

    Groups tasks by dependency level - all tasks at the same level
    can run in parallel. Returns list of groups, where each group
    contains task IDs that can execute in parallel.
    """
    task_map = {task.task_id: task for task in tasks}

    # Calculate in-degree for each task (how many dependencies it has)
    in_degree = {task_id: len(task.dependencies) for task_id, task in task_map.items()}

    # Topological sort - group by level
    level_groups: List[List[str]] = []
    remaining = set(task_map.keys())

    while remaining:
        # Find all tasks with no remaining dependencies (current level)
        current_level = [task_id for task_id in remaining if in_degree[task_id] == 0]

        if not current_level:
            # Circular dependency or error - add remaining tasks
            current_level = list(remaining)

        level_groups.append(current_level)
        remaining -= set(current_level)

        # Decrease in-degree for tasks that depend on current level
        for task_id in current_level:
            for dep_task in tasks:
                if task_id in dep_task.dependencies and dep_task.task_id in remaining:
                    in_degree[dep_task.task_id] -= 1

    # Return groups with more than one task (parallelizable)
    return [group for group in level_groups if len(group) > 1]


@planning_router.reasoner()
async def create_research_plan(
    research_question: str,
    max_depth: int = 3,
    max_tasks_per_level: int = 5,
) -> ResearchPlan:
    """
    Create a recursive research plan by breaking down a question into subtasks.

    This reasoner recursively decomposes a research question into smaller,
    manageable subtasks, forming a topological graph that can be executed
    in parallel where dependencies allow.
    """
    # First, get initial breakdown from LLM - simplified to just descriptions
    initial_response = await planning_router.ai(
        system=(
            "You are an expert research planner breaking down questions into a hierarchical task graph.\n\n"
            "## PHILOSOPHY\n"
            "You are creating two types of tasks:\n"
            "1. **Leaf tasks** (no dependencies) = Specific questions that need web search\n"
            "   - These are atomic research questions answerable via web search\n"
            "   - Example: 'What is AgentField?' or 'What are AgentField's features?'\n\n"
            "2. **Parent tasks** (have dependencies) = Questions answered by synthesizing children\n"
            "   - These combine answers from child tasks\n"
            "   - Example: 'Summarize AgentField' depends on 'What is AgentField?' and 'What are features?'\n\n"
            "## DEPENDENCY MEANING\n"
            "A task depends on another if it needs that task's ANSWER to proceed.\n"
            "Dependencies mean: 'I need answers from those tasks to answer this.'\n\n"
            "## YOUR TASK\n"
            "Break the research question into 3-5 major research areas.\n"
            "Each area should be a specific, searchable question (leaf task).\n"
            "These will be refined recursively, and synthesis tasks will be created later.\n\n"
            f"Maximum {max_tasks_per_level} tasks.\n\n"
            "Return ONLY a JSON object with a 'descriptions' array."
        ),
        user=(
            f"Research Question: {research_question}\n\n"
            f"Break this into 3-5 major research areas as specific, searchable questions. "
            f"Return only the descriptions array."
        ),
        schema=TaskDescriptions,
    )

    # Build initial Subtask objects from descriptions
    initial_plan = [
        Subtask(
            task_id=f"task_{idx + 1}",
            description=desc,
            dependencies=[],
            depth=1,
            can_parallelize=True,
        )
        for idx, desc in enumerate(initial_response.descriptions)
    ]

    # Recursively refine each task
    all_tasks: List[Subtask] = []

    async def refine_recursively(
        task: Subtask, parent_context: str = ""
    ) -> List[Subtask]:
        """Recursively refine a task by calling the refine_task reasoner."""
        if task.depth >= max_depth:
            # Base case: task is specific enough
            return [task]

        # Directly call the refine_task reasoner - this creates a workflow node
        refined_tasks = await refine_task(
            task_description=task.description,
            parent_context=parent_context or research_question,
            current_depth=task.depth,
            max_depth=max_depth,
        )

        # Update task IDs to maintain hierarchy and recursively refine
        result_tasks: List[Subtask] = []
        for idx, refined_task in enumerate(refined_tasks):
            new_task_id = f"{task.task_id}_{idx + 1}"
            new_task = Subtask(
                task_id=new_task_id,
                description=refined_task.description,
                dependencies=refined_task.dependencies,
                depth=task.depth + 1,
                can_parallelize=len(refined_task.dependencies) == 0,
            )

            # Recursively refine if still not at max depth
            if new_task.depth < max_depth:
                further_refined = await refine_recursively(new_task, task.description)
                result_tasks.extend(further_refined)
            else:
                result_tasks.append(new_task)

        # If no refinement happened, return the original task
        return result_tasks if result_tasks else [task]

    # Refine initial tasks - can run in parallel since they're independent
    refinement_tasks = [
        refine_recursively(initial_task, research_question)
        for initial_task in initial_plan
    ]
    refined_results = await asyncio.gather(*refinement_tasks)

    # Flatten the results
    for refined_list in refined_results:
        all_tasks.extend(refined_list)

    # Identify dependencies between tasks
    tasks_for_analysis = [
        {"task_id": task.task_id, "description": task.description} for task in all_tasks
    ]
    dependencies_response = await identify_dependencies(
        tasks_for_analysis, research_question
    )

    # Update task dependencies
    task_map = {task.task_id: task for task in all_tasks}
    dependency_map = {
        dep.task_id: dep.depends_on for dep in dependencies_response.dependencies
    }

    for task in all_tasks:
        if task.task_id in dependency_map:
            task.dependencies = dependency_map[task.task_id]
            # Validate dependencies exist
            task.dependencies = [dep for dep in task.dependencies if dep in task_map]
            task.can_parallelize = len(task.dependencies) == 0

    # Build topological groups using topological sort
    parallelizable_groups = _build_topological_groups(all_tasks)

    return ResearchPlan(
        research_question=research_question,
        tasks=all_tasks,
        max_depth=max(task.depth for task in all_tasks) if all_tasks else 0,
        total_tasks=len(all_tasks),
        parallelizable_groups=parallelizable_groups,
    )


@planning_router.reasoner()
async def refine_task(
    task_description: str,
    parent_context: str = "",
    current_depth: int = 0,
    max_depth: int = 3,
) -> List[Subtask]:
    """
    Recursively refine a single task into smaller subtasks.

    This is a helper reasoner that can be called recursively to break down
    complex tasks into more manageable pieces. Each call creates a workflow node.
    """

    if current_depth >= max_depth:
        # Return the task as-is if we've hit max depth
        return [
            Subtask(
                task_id=f"leaf_{current_depth}",
                description=task_description,
                dependencies=[],
                depth=current_depth,
                can_parallelize=True,
            )
        ]

    # Use AI to determine if task needs further breakdown - simplified schema
    result_response = await planning_router.ai(
        system=(
            "You are a task decomposition expert. Break down research tasks into "
            "smaller subtasks.\n\n"
            "Return ONLY a JSON object with a 'descriptions' array.\n"
            "- If the task is specific enough, return it as a single-item array\n"
            "- If it needs breakdown, return 2-4 smaller task descriptions\n"
            "- Each description should be independently researchable\n\n"
            f"Current depth: {current_depth} of {max_depth}. "
            f"Only break down if still too complex."
        ),
        user=(
            f"Task: {task_description}\n"
            f"{f'Context: {parent_context}' if parent_context else ''}\n\n"
            f"Break this into smaller tasks if needed, or return as-is if specific enough."
        ),
        schema=TaskDescriptions,
    )

    # Build Subtask objects from descriptions
    refined_tasks = [
        Subtask(
            task_id=f"subtask_{idx}",
            description=desc,
            dependencies=[],
            depth=current_depth + 1,
            can_parallelize=True,
        )
        for idx, desc in enumerate(result_response.descriptions)
    ]

    return refined_tasks


@planning_router.reasoner()
async def identify_dependencies(
    tasks: List[dict], research_question: str
) -> TaskDependenciesList:
    """
    Identify dependencies between tasks based on their descriptions.

    Takes a list of tasks with id and description, and identifies which
    tasks need results from other tasks before they can execute.
    """
    # Format tasks for the prompt
    tasks_text = "\n".join(
        f"- {task['task_id']}: {task['description']}" for task in tasks
    )

    response = await planning_router.ai(
        system=(
            "You are a dependency analysis expert identifying task relationships.\n\n"
            "## DEPENDENCY PHILOSOPHY\n"
            "A task depends on another if it needs that task's ANSWER to proceed.\n"
            "Dependencies mean: 'I need answers from those tasks to answer this.'\n\n"
            "## DEPENDENCY PATTERNS\n"
            "- **Comparison tasks** depend on individual research tasks\n"
            "  Example: 'Compare X and Y' depends on 'What is X?' and 'What is Y?'\n\n"
            "- **Synthesis tasks** depend on all component tasks\n"
            "  Example: 'Summarize AgentField' depends on 'What is AgentField?' and 'What are features?'\n\n"
            "- **Analysis tasks** depend on data-gathering tasks\n"
            "  Example: 'Analyze trends' depends on 'What are the trends?'\n\n"
            "## KEY PRINCIPLE\n"
            "If a task can be answered by combining other tasks' findings, mark dependencies.\n"
            "Leaf tasks (no dependencies) will be answered via web search.\n"
            "Parent tasks (have dependencies) will synthesize from children's answers.\n\n"
            "Return ONLY a JSON object with a 'dependencies' array. Each item:\n"
            "- task_id: the task ID\n"
            "- depends_on: array of task IDs it depends on (empty if independent/leaf task)\n\n"
            "Be conservative - only mark dependencies when clearly needed."
        ),
        user=(
            f"Research Question: {research_question}\n\n"
            f"Tasks:\n{tasks_text}\n\n"
            f"Identify dependencies. For each task, determine if it needs answers from other tasks. "
            f"Return dependency mappings for all tasks."
        ),
        schema=TaskDependenciesList,
    )

    return response
