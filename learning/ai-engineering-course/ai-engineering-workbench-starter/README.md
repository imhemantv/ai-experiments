# AI Engineering Workbench Starter

This is the executable starting point for Module 1 of the interactive AI
Application Engineer course.

It runs offline by default through a deterministic fake provider, so the
gateway contract, telemetry, tests, and CLI can be exercised without an API
key or paid dependency.

## Run

```powershell
cd ai-engineering-workbench-starter
py -3.12 -m pip install -e .
py -3.12 -m unittest discover -s tests -v
py -3.12 -m workbench.cli --prompt "Explain idempotency in one sentence."
py -3.12 -m workbench.cli benchmark --cases 300 --out artifacts\module-01\runs.jsonl
py -3.12 -m workbench.evidence --module foundations artifacts\module-01\evidence.json
```

The benchmark writes deterministic JSONL traces and a validated
`artifacts/module-01/evidence.json` manifest.

## Scaffold Modules 2-10

Create a module only when you are ready to start it:

```powershell
py -3.12 -m workbench.scaffold --module 2
py -3.12 -m unittest discover -s tests -p test_extraction_api.py -v
```

The generator uses the exact paths documented by the course. It creates a
package stub, positive and adversarial evaluation cases, evidence schema,
evidence template, command stubs where applicable, and a contract test with
module-specific evidence assertions. The new test intentionally fails until
you implement the documented contract. The generator refuses to overwrite
existing learner work. Repeat `--module` to scaffold several modules in one
command.

Course maintainers verify the downloadable archive after rebuilding it:

```powershell
py -3.12 scripts\verify_distribution.py
```

## Add a real provider

Implement the `ModelProvider` protocol in `workbench/gateway.py`. Keep SDK
objects inside the adapter and return only the provider-neutral `ModelResult`.
Read credentials from environment variables; never commit them.

## Learning rule

For every change:

1. State the hypothesis.
2. Change one independent variable.
3. Run a fixed case set.
4. Save raw results.
5. Explain what the evidence supports and what it does not.

The interactive course also requires an independently reviewed cold task for
each module. The multiple domains are deliberate transfer exercises inside one
shared engineering workbench; reuse common contracts, evidence, identity,
evaluation, security, and platform code rather than building isolated demos.
