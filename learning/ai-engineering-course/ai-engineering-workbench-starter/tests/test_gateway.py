import json
import tempfile
import unittest
from pathlib import Path

from workbench.cli import run_benchmark
from workbench.contracts import ModelRequest
from workbench.gateway import ModelGateway, OfflineProvider
from workbench.evidence import validate_manifest
from workbench.telemetry import append_run


class ModelGatewayTests(unittest.TestCase):
    def test_returns_provider_neutral_telemetry(self) -> None:
        request = ModelRequest(prompt="  explain   tokens  ")
        result = ModelGateway(OfflineProvider()).complete(request)

        self.assertEqual("offline-demo", result.model)
        self.assertTrue(result.request_id.startswith("offline-"))
        self.assertGreater(result.usage.input_tokens, 0)
        self.assertGreaterEqual(result.latency_ms, 0)

    def test_trace_is_written_as_jsonl(self) -> None:
        request = ModelRequest(prompt="trace this")
        result = ModelGateway(OfflineProvider()).complete(request)

        with tempfile.TemporaryDirectory() as directory:
            trace = Path(directory) / "runs.jsonl"
            append_run(trace, request, result)
            content = trace.read_text(encoding="utf-8")

        self.assertIn(result.request_id, content)
        self.assertIn('"input_tokens"', content)

    def test_evidence_manifest_requires_reproducibility_fields(self) -> None:
        errors = validate_manifest({
            "module": "foundations",
            "sample_size": 50,
            "command_status": "failed",
            "metrics": {},
            "failures": [],
        })

        self.assertIn("missing field: dataset_hash", errors)
        self.assertIn("protocol must be an object", errors)
        self.assertIn("statistics must be an object", errors)
        self.assertIn("command_status must be 'passed'", errors)
        self.assertIn("metrics must be a non-empty object", errors)

    def test_benchmark_command_writes_valid_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            trace = Path(directory) / "artifacts" / "module-01" / "runs.jsonl"
            run_benchmark(["--cases", "5", "--out", str(trace)])
            evidence = json.loads((trace.parent / "evidence.json").read_text(encoding="utf-8"))
            trace_lines = trace.read_text(encoding="utf-8").splitlines()
            dataset_lines = (trace.parent / "dataset.jsonl").read_text(encoding="utf-8").splitlines()
            validation_errors = validate_manifest(evidence, trace.parent, expected_module="foundations")

        self.assertEqual([], validation_errors)
        self.assertEqual(5, evidence["sample_size"])
        self.assertEqual(5, len(trace_lines))
        self.assertEqual(5, len(dataset_lines))

    def test_evidence_rejects_fabrication_and_placeholders(self) -> None:
        fabricated = {
            "module": "foundations",
            "dataset_hash": "replace-with-sha256",
            "system_version": "replace-with-version",
            "sample_size": 300,
            "command": "replace-with-command",
            "command_status": "passed",
            "metrics": {"invented_percent": 100.0},
            "statistics": {
                "numerator": 1,
                "denominator": 1,
                "metric": "invented_percent",
                "confidence_method": "replace-with-method",
            },
            "artifacts": [
                {
                    "role": "run_records",
                    "path": "replace-with-path",
                    "sha256": "replace-with-hash",
                }
            ],
            "failures": [],
            "protocol": {
                "declared_before_run": True,
                "baseline": "replace-with-baseline",
                "candidate": "replace-with-candidate",
                "holdout_used_for_tuning": True,
                "confidence_method": "replace-with-method",
            },
        }
        errors = validate_manifest(fabricated)

        self.assertIn("dataset_hash contains a placeholder", errors)
        self.assertIn("statistics.denominator must equal sample_size", errors)
        self.assertIn("protocol.holdout_used_for_tuning must be false for completion evidence", errors)
        self.assertIn("artifact 0 path must be a non-placeholder string", errors)

    def test_evidence_rejects_unrelated_artifacts_and_invented_metrics(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            dataset = root / "dataset.jsonl"
            runs = root / "runs.jsonl"
            dataset.write_text('{"case_id":"case-0000","prompt":"real prompt"}\n', encoding="utf-8")
            runs.write_text(
                '{"request":{"prompt":"different prompt"},"result":{"request_id":"id-1","latency_ms":7}}\n',
                encoding="utf-8",
            )
            import hashlib

            manifest = {
                "module": "foundations",
                "dataset_hash": hashlib.sha256(dataset.read_bytes()).hexdigest(),
                "system_version": "offline-provider-v1",
                "sample_size": 1,
                "command": "python -m workbench.cli benchmark --cases 1 --out runs.jsonl",
                "command_status": "passed",
                "metrics": {
                    "schema_validity_percent": 50.0,
                    "unique_request_id_percent": 50.0,
                    "p95_latency_ms": 999,
                },
                "statistics": {
                    "numerator": 1,
                    "denominator": 1,
                    "metric": "schema_validity_percent",
                    "confidence_method": "exact binomial",
                },
                "artifacts": [
                    {
                        "role": "dataset",
                        "path": dataset.name,
                        "sha256": hashlib.sha256(dataset.read_bytes()).hexdigest(),
                        "line_count": 1,
                    },
                    {
                        "role": "run_records",
                        "path": runs.name,
                        "sha256": hashlib.sha256(runs.read_bytes()).hexdigest(),
                        "line_count": 1,
                    },
                ],
                "failures": [],
                "protocol": {
                    "declared_before_run": True,
                    "baseline": "offline-provider-v1",
                    "candidate": "offline-provider-v1",
                    "holdout_used_for_tuning": False,
                    "confidence_method": "deterministic census",
                },
            }
            errors = validate_manifest(manifest, root)

        self.assertIn("run_records prompts must match the dataset in order", errors)
        self.assertIn("metric 'schema_validity_percent' does not match run_records", errors)
        self.assertIn("metric 'p95_latency_ms' does not match run_records", errors)

    def test_expected_module_prevents_validation_bypass(self) -> None:
        errors = validate_manifest(
            {
                "module": "capstone",
                "dataset_hash": "0" * 64,
                "system_version": "offline-provider-v1",
                "sample_size": 1,
                "command": "python -m workbench.cli benchmark --cases 1 --out runs.jsonl",
                "command_status": "passed",
                "metrics": {"invented_metric": 987654},
                "statistics": {
                    "numerator": 1,
                    "denominator": 1,
                    "metric": "invented_metric",
                    "confidence_method": "exact binomial",
                },
                "artifacts": [
                    {"role": "dataset", "path": "dataset.jsonl", "sha256": "0" * 64},
                    {"role": "run_records", "path": "runs.jsonl", "sha256": "1" * 64},
                ],
                "failures": [],
                "protocol": {
                    "declared_before_run": True,
                    "baseline": "offline-provider-v1",
                    "candidate": "offline-provider-v1",
                    "holdout_used_for_tuning": False,
                    "confidence_method": "deterministic census",
                },
            },
            expected_module="foundations",
        )

        self.assertIn("module must match expected module 'foundations'", errors)


if __name__ == "__main__":
    unittest.main()
