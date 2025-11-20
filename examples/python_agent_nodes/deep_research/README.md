# Deep Research Agent (Recursive Planning)

A research agent that uses recursive planning to break down complex research questions into manageable subtasks, forming a topological graph that can be executed in parallel.

## Highlights

- **Recursive Planning** – Automatically breaks down research questions into subtasks with configurable depth
- **Topological Graph** – Identifies task dependencies and parallelization opportunities
- **Simple & Elegant** – Uses AgentField primitives for clean, maintainable code
- **Single Router Architecture** – All planning logic in one router for simplicity

## Architecture

### Recursive Planning System

1. **Research Plan Creation** (`create_research_plan`)
   - Takes a research question and breaks it down recursively
   - Identifies dependencies between tasks
   - Groups tasks for parallel execution
   - Returns a complete `ResearchPlan` with topological structure

2. **Task Refinement** (`refine_task`)
   - Helper reasoner for recursive task decomposition
   - Can be called to further break down complex tasks
   - Respects maximum depth constraints

## Project Structure

```
deep_research/
├── main.py            # Agent bootstrap
├── schemas.py         # Pydantic models for planning
├── routers/
│   ├── __init__.py
│   └── planning.py    # Recursive planning router
├── requirements.txt
└── README.md
```

## Quick Start

### 1. Install Dependencies

```bash
pip install -r examples/python_agent_nodes/deep_research/requirements.txt
```

### 2. Run the Agent

```bash
python examples/python_agent_nodes/deep_research/main.py
```

### 3. Create a Research Plan

POST to `/reasoners/planning_create_research_plan`:

```json
{
  "research_question": "What are the environmental impacts of electric vehicles compared to traditional vehicles?",
  "max_depth": 3,
  "max_tasks_per_level": 5
}
```

### Response Format

```json
{
  "research_question": "What are the environmental impacts of electric vehicles compared to traditional vehicles?",
  "tasks": [
    {
      "task_id": "task_1",
      "description": "Research manufacturing environmental impact of EVs",
      "dependencies": [],
      "depth": 1,
      "can_parallelize": true
    },
    {
      "task_id": "task_2",
      "description": "Research manufacturing environmental impact of traditional vehicles",
      "dependencies": [],
      "depth": 1,
      "can_parallelize": true
    },
    {
      "task_id": "task_3",
      "description": "Research operational emissions of EVs",
      "dependencies": [],
      "depth": 1,
      "can_parallelize": true
    },
    {
      "task_id": "task_4",
      "description": "Compare manufacturing impacts",
      "dependencies": ["task_1", "task_2"],
      "depth": 2,
      "can_parallelize": false
    },
    {
      "task_id": "task_5",
      "description": "Synthesize overall comparison",
      "dependencies": ["task_3", "task_4"],
      "depth": 3,
      "can_parallelize": false
    }
  ],
  "max_depth": 3,
  "total_tasks": 5,
  "parallelizable_groups": [
    ["task_1", "task_2", "task_3"],
    ["task_4"],
    ["task_5"]
  ]
}
```

## Available Endpoints

### Reasoners

- **`/reasoners/planning_create_research_plan`** – Create a recursive research plan
  - Parameters: `research_question`, `max_depth` (default: 3), `max_tasks_per_level` (default: 5)
  - Returns: `ResearchPlan` with tasks, dependencies, and parallelization groups

- **`/reasoners/planning_refine_task`** – Recursively refine a single task
  - Parameters: `task_description`, `parent_context`, `current_depth`, `max_depth`
  - Returns: List of `Subtask` objects

## Design Notes

### Recursive Planning Strategy

The planner uses a hierarchical approach:
1. **Top-level decomposition**: Break the main question into 3-5 major areas
2. **Recursive refinement**: For each area, break it down further if needed
3. **Dependency identification**: Determine which tasks need results from others
4. **Parallelization grouping**: Group tasks that can run simultaneously

### Task Dependencies

- **Independent tasks**: No dependencies, can run in parallel
- **Sequential tasks**: Depend on one or more previous tasks
- **Synthesis tasks**: Typically depend on all component tasks

### Topological Graph

The plan forms a DAG (Directed Acyclic Graph) where:
- Nodes are tasks
- Edges are dependencies
- Tasks at the same level with no dependencies can run in parallel
- The `parallelizable_groups` field identifies execution batches

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `AGENTFIELD_SERVER` | Control plane server URL | `http://localhost:8080` |
| `AI_MODEL` | Primary LLM | `openrouter/openai/gpt-4o-mini` |
| `PORT` | Agent server port | Auto-assigned |

## Next Steps

- Add task execution reasoners to actually perform research
- Implement parallel execution using AgentField's workflow capabilities
- Add result synthesis to combine findings from all tasks
- Create visualization tools for the task graph
- Add progress tracking and checkpointing
