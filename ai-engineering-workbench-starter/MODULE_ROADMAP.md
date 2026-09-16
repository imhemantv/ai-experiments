# Cumulative module roadmap

Keep one repository and evolve it through the course. Do not create ten
unrelated demos. The repository intentionally contains several integrated
domain exemplars rather than pretending invoices, enterprise search, support
workflows, and repository agents are one product. Shared gateway, identity,
evaluation, evidence, security, and platform mechanisms should be reused.

| Module | Package added | Required offline contract |
|---|---|---|
| 1 | `gateway`, `contracts`, `telemetry` | Provider isolation, deadlines, typed errors, trace output |
| 2 | `extraction` | Schema and domain validation, review routing, multimodal fixtures |
| 3 | `rag` | Stable ingestion, lexical/vector/hybrid retrieval, ACL filtering, citations |
| 4 | `workflows` | Durable state, idempotency, approval binding, crash recovery |
| 5 | `agent` | Typed tools, MCP adapter, budgets, sandbox, checkpoint/resume |
| 6 | `evals` | Versioned cases, graders, repeated trials, confidence bounds, reports |
| 7 | `platform` | Routing, quotas, queues, traces, canary, rollback, load and soak |
| 8 | `security` | Identity, policy, egress, red-team corpus, incident evidence |
| 9 | `architecture` | Sizing, cost, options, ADRs, rollout, cross-functional review |
| 10 | `capstone` | Deployed product, holdout, external pilot, dossier and mocks |

For every module:

1. Add failing contract tests before the implementation.
2. Keep tests offline and deterministic by default.
3. Put paid/provider integration tests behind an explicit environment flag.
4. Generate `evidence.json` using the schema demonstrated in
   `examples/evidence-manifest.json`, including successful/total counts and the
   confidence method used for reported bounds.
5. Commit raw reports under `artifacts/` only when they contain no secrets or
   sensitive user data.
6. Complete the module's cold judgment task and obtain an independent rubric
   score before recording course attestation.

After the common core, select at least one specialization: realtime/voice
product engineering, agent runtimes and multi-agent comparison, open-model
adaptation, or open-source inference optimization. These extensions belong in
the same workbench but are not required for every applied-AI role.

Run `py -3.12 -m workbench.scaffold --module N` at the start of Modules 2-10.
It creates the package, red contract test, seeded case, evidence schema, and
manifest template without giving away the implementation. The interactive
course provides the invariants, experiments, and commands for each increment.
