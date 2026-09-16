from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ModuleScaffold:
    number: int
    module_id: str
    package: str
    contract: str
    test_path: str
    cases_path: str
    required_evidence: tuple[str, ...]
    command_modules: tuple[str, ...] = ()


MODULES = {
    module.number: module
    for module in (
        ModuleScaffold(
            2,
            "patterns",
            "extraction",
            "Extract a typed invoice or route it to review.",
            "tests/test_extraction_api.py",
            "evals/invoice_cases.jsonl",
            ("decision", "validation_errors", "source_evidence"),
            ("replay",),
        ),
        ModuleScaffold(
            3,
            "rag",
            "rag",
            "Retrieve authorized evidence and return verifiable citations.",
            "tests/rag/test_contract.py",
            "evals/rag_queries.jsonl",
            ("authorized_chunk_ids", "citations", "abstained"),
            ("evaluate",),
        ),
        ModuleScaffold(
            4,
            "workflows",
            "workflows",
            "Resume an idempotent workflow after a crash.",
            "tests/workflows/test_contract.py",
            "evals/workflow_cases.jsonl",
            ("final_state", "side_effect_count", "audit_events"),
            ("chaos",),
        ),
        ModuleScaffold(
            5,
            "agents",
            "agent",
            "Complete a bounded repository task without an unsafe action.",
            "tests/agent/test_contract.py",
            "benchmarks/agent_tasks.jsonl",
            ("stop_reason", "steps", "unsafe_actions"),
            ("benchmark",),
        ),
        ModuleScaffold(
            6,
            "evals",
            "evals",
            "Run versioned cases and produce uncertainty-aware release evidence.",
            "tests/evals/test_contract.py",
            "evals/cases/contract.jsonl",
            ("dataset_version", "confidence_interval", "gate_decision"),
            ("runner",),
        ),
        ModuleScaffold(
            7,
            "production",
            "platform",
            "Route requests under declared SLO, capacity, and cost limits.",
            "tests/platform/test_contract.py",
            "load/platform_cases.jsonl",
            ("route", "latency_ms", "cost_usd"),
        ),
        ModuleScaffold(
            8,
            "security",
            "security",
            "Authorize every side effect and preserve tenant isolation.",
            "tests/security/test_contract.py",
            "security/payloads/injection.jsonl",
            ("decision", "policy_reason", "audit_event"),
            ("redteam",),
        ),
        ModuleScaffold(
            9,
            "design",
            "architecture",
            "Produce a quantified architecture decision packet.",
            "tests/architecture/test_contract.py",
            "architecture/cases.jsonl",
            ("assumptions", "capacity", "decision"),
            ("check", "cost"),
        ),
        ModuleScaffold(
            10,
            "capstone",
            "capstone",
            "Package product, holdout, pilot, and operational evidence.",
            "tests/capstone/test_contract.py",
            "capstone/evals/holdout.jsonl",
            ("holdout_result", "security_result", "rollback_verified"),
        ),
    )
}


def _write_new(path: Path, content: str) -> None:
    if path.exists():
        raise FileExistsError(f"refusing to overwrite existing file: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _cases(module: ModuleScaffold) -> str:
    cases = (
        {
            "id": f"{module.module_id}-positive-001",
            "module": module.module_id,
            "risk": "medium",
            "input": {"scenario": "authorized_valid_request"},
            "expected": {"passed": True},
        },
        {
            "id": f"{module.module_id}-adversarial-001",
            "module": module.module_id,
            "risk": "high",
            "input": {"scenario": "invalid_or_unauthorized_request"},
            "expected": {"passed": False},
        },
    )
    return "".join(json.dumps(case) + "\n" for case in cases)


def _contract_test(module: ModuleScaffold) -> str:
    evidence_keys = repr(set(module.required_evidence))
    return (
        "import json\n"
        "import unittest\n"
        "from pathlib import Path\n\n"
        f"from workbench.{module.package}.contracts import run_contract\n\n\n"
        "class ModuleContractTests(unittest.TestCase):\n"
        "    def test_seeded_positive_and_adversarial_cases(self) -> None:\n"
        f'        case_path = Path(r"{module.cases_path}")\n'
        '        cases = [json.loads(line) for line in case_path.read_text(encoding="utf-8").splitlines()]\n'
        "        self.assertEqual(2, len(cases))\n"
        "        for case in cases:\n"
        "            with self.subTest(case=case['id']):\n"
        "                result = run_contract(case)\n"
        "                self.assertEqual(case['expected']['passed'], result.passed)\n"
        "                if result.passed:\n"
        f"                    self.assertTrue({evidence_keys}.issubset(result.evidence))\n"
        "                else:\n"
        "                    self.assertTrue(result.evidence.get('reason'))\n\n\n"
        'if __name__ == "__main__":\n'
        "    unittest.main()\n"
    )


def _evidence_schema(module: ModuleScaffold) -> str:
    return (
        json.dumps(
            {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "type": "object",
                "required": [
                    "module",
                    "dataset_hash",
                    "system_version",
                    "sample_size",
                    "command",
                    "command_status",
                    "metrics",
                    "statistics",
                    "artifacts",
                    "failures",
                    "protocol",
                ],
                "properties": {
                    "module": {"const": module.module_id},
                    "dataset_hash": {"type": "string", "minLength": 8},
                    "system_version": {"type": "string", "minLength": 1},
                    "sample_size": {"type": "integer", "minimum": 0},
                    "command": {"type": "string", "minLength": 1},
                    "command_status": {"enum": ["not-run", "failed", "passed"]},
                    "metrics": {"type": "object"},
                    "statistics": {
                        "type": "object",
                        "required": ["numerator", "denominator", "metric", "confidence_method"],
                        "properties": {
                            "numerator": {"type": "integer", "minimum": 0},
                            "denominator": {"type": "integer", "minimum": 1},
                            "metric": {"type": "string", "minLength": 1},
                            "confidence_method": {"type": "string", "minLength": 1},
                        },
                    },
                    "artifacts": {
                        "type": "array",
                        "minItems": 1,
                        "items": {
                            "type": "object",
                            "required": ["role", "path", "sha256"],
                            "properties": {
                                "role": {"enum": ["dataset", "run_records"]},
                                "path": {"type": "string", "minLength": 1},
                                "sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                                "line_count": {"type": "integer", "minimum": 0},
                            },
                        },
                    },
                    "failures": {"type": "array"},
                    "protocol": {
                        "type": "object",
                        "required": [
                            "declared_before_run",
                            "baseline",
                            "candidate",
                            "holdout_used_for_tuning",
                            "confidence_method",
                        ],
                        "properties": {
                            "declared_before_run": {"type": "boolean"},
                            "baseline": {"type": "string", "minLength": 1},
                            "candidate": {"type": "string", "minLength": 1},
                            "holdout_used_for_tuning": {"type": "boolean"},
                            "confidence_method": {"type": "string", "minLength": 1},
                        },
                    },
                },
            },
            indent=2,
        )
        + "\n"
    )


def _evidence_template(module: ModuleScaffold) -> str:
    return (
        json.dumps(
            {
                "module": module.module_id,
                "dataset_hash": "replace-with-content-hash",
                "system_version": "replace-with-version-and-environment",
                "sample_size": 0,
                "command": "replace-with-exact-command",
                "command_status": "not-run",
                "metrics": {},
                "statistics": {
                    "numerator": 0,
                    "denominator": 1,
                    "metric": "replace-with-primary-metric-name",
                    "confidence_method": "replace-with-method",
                },
                "artifacts": [
                    {
                        "role": "dataset",
                        "path": module.cases_path,
                        "sha256": "replace-with-dataset-sha256",
                        "line_count": 2,
                    },
                    {
                        "role": "run_records",
                        "path": "replace-with-relative-run-records-path",
                        "sha256": "replace-with-run-records-sha256",
                        "line_count": 0,
                    }
                ],
                "failures": [],
                "protocol": {
                    "declared_before_run": True,
                    "baseline": "replace-with-baseline",
                    "candidate": "replace-with-candidate",
                    "holdout_used_for_tuning": False,
                    "confidence_method": "replace-with-method",
                },
            },
            indent=2,
        )
        + "\n"
    )


def scaffold_module(root: Path, module_number: int) -> list[Path]:
    module = MODULES[module_number]
    package_root = root / "src" / "workbench" / module.package
    root_package = root / "src" / "workbench" / "__init__.py"
    files = {
        package_root / "__init__.py": '"""Course scaffold. Replace placeholders while preserving the contract."""\n',
        package_root / "contracts.py": (
            "from dataclasses import dataclass\n\n\n"
            "@dataclass(frozen=True)\n"
            "class ContractResult:\n"
            "    passed: bool\n"
            "    evidence: dict[str, object]\n\n\n"
            "def run_contract(case: dict[str, object]) -> ContractResult:\n"
            f'    """{module.contract}"""\n'
            '    raise NotImplementedError("implement this module contract")\n'
        ),
        root / module.test_path: _contract_test(module),
        root / module.cases_path: _cases(module),
        root / "schemas" / f"module-{module.number:02d}-evidence.schema.json": _evidence_schema(module),
        root / "examples" / f"module-{module.number:02d}-evidence-template.json": _evidence_template(module),
    }
    if not root_package.exists():
        files[root_package] = '"""AI Engineering Workbench."""\n'
    for command_module in module.command_modules:
        files[package_root / f"{command_module}.py"] = (
            f'"""Command scaffold for Module {module.number}; implement before running the course verification command."""\n\n'
            "def main() -> None:\n"
            '    raise SystemExit("not implemented: satisfy the red contract tests first")\n\n\n'
            'if __name__ == "__main__":\n'
            "    main()\n"
        )

    for path, content in files.items():
        _write_new(path, content)
    return list(files)


def main() -> int:
    parser = argparse.ArgumentParser(description="Create the next course module's red test scaffold.")
    parser.add_argument("--module", type=int, choices=sorted(MODULES), action="append", required=True)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()

    created: list[Path] = []
    for module_number in args.module:
        created.extend(scaffold_module(args.root.resolve(), module_number))
    for path in created:
        print(path.relative_to(args.root.resolve()))
    print("The generated contract tests and command stubs should fail until you implement the module.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
