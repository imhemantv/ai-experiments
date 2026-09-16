# AI Engineering Course for Software Developers

A project-first, self-paced course for experienced software engineers moving
into applied AI engineering. The curriculum emphasizes executable systems,
controlled experiments, measurable benchmarks, failure analysis, production
operations, security, and interview defense rather than model training or
data-science workflows.

## Start the course

Open `index.html` in a browser:

```powershell
Start-Process .\index.html
```

Progress, notes, benchmark results, and evidence attestations are stored in
the browser's local storage.

## Starter workbench

The repository includes:

- `ai-engineering-workbench-starter\` - editable Python source and tests
- `ai-engineering-workbench-starter.zip` - downloadable clean starter archive

Run the starter:

```powershell
cd .\ai-engineering-workbench-starter
py -3.12 -m pip install -e .
py -3.12 -m unittest discover -s tests -v
py -3.12 -m workbench.cli benchmark --cases 300 --out artifacts\module-01\runs.jsonl
py -3.12 -m workbench.evidence --module foundations artifacts\module-01\evidence.json
```

## Learning standard

For every module:

1. State a falsifiable hypothesis.
2. Change one independent variable.
3. Run fixed positive, adversarial, and failure cases.
4. Preserve raw traces and machine-checkable evidence.
5. Explain what the results support and what they do not.
6. Defend the design and tradeoffs in an independently reviewed cold task.

