# AI Experiments

This repository is my engineering workspace for learning, building, measuring,
and documenting applied AI systems.

The goal is not to collect isolated demos. Each project should test a clear
hypothesis, preserve reproducible evidence, expose failure modes, and produce
an engineering decision that can survive review.

## Repository structure

| Area | Purpose |
|---|---|
| [`experiments/`](experiments/) | Runnable investigations of models, prompts, retrieval, agents, evaluation, safety, latency, and cost |
| [`benchmarks/`](benchmarks/) | Reusable datasets, protocols, result summaries, and comparisons across experiments |
| [`learning/`](learning/) | Structured learning programs and implementation exercises |
| [`notes/`](notes/) | Architecture decisions, paper breakdowns, interview defenses, and lessons from failed experiments |

## Current work

### Learning

- [AI Engineering for Software Developers](learning/ai-engineering-course/) -
  an interactive, project-first learning path with a runnable Python workbench,
  benchmarks, evidence gates, production exercises, and interview defense.

### Experiments

New experiment projects will be indexed here as they are added.

## Experiment standard

Every meaningful experiment should record:

1. **Question** - the decision or uncertainty being investigated.
2. **Hypothesis** - a falsifiable prediction made before running the test.
3. **Protocol** - fixed inputs, baselines, metrics, environment, and stopping criteria.
4. **Execution** - reproducible commands and versioned code.
5. **Evidence** - raw traces, aggregate metrics, failures, and uncertainty.
6. **Decision** - what changed because of the result and what remains unknown.

Use the template in [`experiments/README.md`](experiments/README.md) when
starting a new investigation.

