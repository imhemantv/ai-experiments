# Experiments

Each subdirectory should be an independently runnable investigation rather
than an unmeasured demo.

## Suggested layout

```text
experiment-name/
  README.md
  src/
  tests/
  data/
  artifacts/
```

Keep large or sensitive datasets and generated artifacts out of Git unless
they are intentionally curated for reproducibility.

## Experiment README template

```markdown
# Experiment title

## Question
What engineering decision will this experiment inform?

## Hypothesis
What result do I predict before running it?

## Baselines and variables
What remains fixed, and what single variable changes?

## Metrics and gates
Which quality, safety, latency, and cost measurements determine the outcome?

## Reproduce
Exact environment and commands.

## Results
Raw artifact locations and summarized measurements.

## Failure analysis
Which cases failed, and why?

## Decision
What does the evidence support, reject, or leave unresolved?
```

