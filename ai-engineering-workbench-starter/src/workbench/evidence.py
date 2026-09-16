import argparse
import json
import hashlib
import math
import re
from pathlib import Path


REQUIRED_FIELDS = {
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
}

PLACEHOLDER_MARKERS = ("replace-with", "placeholder", "example-value", "todo", "tbd")
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
REQUIRED_ARTIFACT_ROLES = {"dataset", "run_records"}
KNOWN_MODULES = {
    "foundations",
    "patterns",
    "rag",
    "workflows",
    "agents",
    "evals",
    "production",
    "security",
    "design",
    "capstone",
}


def _is_placeholder(value: str) -> bool:
    normalized = value.strip().lower()
    return not normalized or any(marker in normalized for marker in PLACEHOLDER_MARKERS)


def _read_jsonl(path: Path, label: str, errors: list[str]) -> list[dict]:
    records = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            errors.append(f"{label} line {line_number} is not valid JSON")
            continue
        if not isinstance(record, dict):
            errors.append(f"{label} line {line_number} must be a JSON object")
            continue
        records.append(record)
    return records


def _validate_foundations_records(
    manifest: dict, dataset_path: Path, run_path: Path, errors: list[str]
) -> None:
    dataset = _read_jsonl(dataset_path, "dataset", errors)
    runs = _read_jsonl(run_path, "run_records", errors)
    sample_size = manifest.get("sample_size")
    if isinstance(sample_size, int):
        if len(dataset) != sample_size:
            errors.append("dataset record count must equal sample_size")
        if len(runs) != sample_size:
            errors.append("run_records record count must equal sample_size")

    dataset_prompts = []
    case_ids = set()
    for index, record in enumerate(dataset):
        case_id = record.get("case_id")
        prompt = record.get("prompt")
        if not isinstance(case_id, str) or _is_placeholder(case_id):
            errors.append(f"dataset record {index} requires a non-placeholder case_id")
        elif case_id in case_ids:
            errors.append(f"dataset record {index} duplicates case_id")
        else:
            case_ids.add(case_id)
        if not isinstance(prompt, str) or _is_placeholder(prompt):
            errors.append(f"dataset record {index} requires a non-placeholder prompt")
        else:
            dataset_prompts.append(prompt)

    run_prompts = []
    request_ids = set()
    latencies = []
    structurally_valid = 0
    for index, record in enumerate(runs):
        request = record.get("request")
        result = record.get("result")
        if not isinstance(request, dict) or not isinstance(result, dict):
            errors.append(f"run_records record {index} requires request and result objects")
            continue
        prompt = request.get("prompt")
        request_id = result.get("request_id")
        latency = result.get("latency_ms")
        if not isinstance(prompt, str):
            errors.append(f"run_records record {index} requires request.prompt")
            continue
        if not isinstance(request_id, str) or _is_placeholder(request_id):
            errors.append(f"run_records record {index} requires result.request_id")
            continue
        if isinstance(latency, bool) or not isinstance(latency, int) or latency < 0:
            errors.append(f"run_records record {index} requires non-negative result.latency_ms")
            continue
        run_prompts.append(prompt)
        request_ids.add(request_id)
        latencies.append(latency)
        structurally_valid += 1

    if run_prompts != dataset_prompts:
        errors.append("run_records prompts must match the dataset in order")
    metrics = manifest.get("metrics")
    if isinstance(metrics, dict) and isinstance(sample_size, int) and sample_size > 0:
        derived = {
            "schema_validity_percent": round(structurally_valid / sample_size * 100, 2),
            "unique_request_id_percent": round(len(request_ids) / sample_size * 100, 2),
        }
        if latencies:
            ordered = sorted(latencies)
            derived["p95_latency_ms"] = ordered[max(0, math.ceil(len(ordered) * 0.95) - 1)]
        for name, value in derived.items():
            if metrics.get(name) != value:
                errors.append(f"metric {name!r} does not match run_records")
    statistics = manifest.get("statistics")
    if isinstance(statistics, dict) and statistics.get("metric") == "schema_validity_percent":
        if statistics.get("numerator") != structurally_valid:
            errors.append("statistics.numerator does not match valid run_records")


def validate_manifest(
    manifest: dict, base_dir: Path | None = None, expected_module: str | None = None
) -> list[str]:
    errors = [f"missing field: {name}" for name in sorted(REQUIRED_FIELDS - manifest.keys())]
    for field in ("module", "dataset_hash", "system_version", "command"):
        if not isinstance(manifest.get(field), str) or not manifest.get(field, "").strip():
            errors.append(f"{field} must be a non-empty string")
        elif _is_placeholder(manifest[field]):
            errors.append(f"{field} contains a placeholder")
    module = manifest.get("module")
    if isinstance(module, str) and module not in KNOWN_MODULES:
        errors.append(f"module must be one of: {', '.join(sorted(KNOWN_MODULES))}")
    if expected_module is not None:
        if expected_module not in KNOWN_MODULES:
            errors.append(f"unknown expected module: {expected_module}")
        elif module != expected_module:
            errors.append(f"module must match expected module {expected_module!r}")
    dataset_hash = manifest.get("dataset_hash")
    if isinstance(dataset_hash, str) and not SHA256_PATTERN.fullmatch(dataset_hash.lower()):
        errors.append("dataset_hash must be a 64-character SHA-256 hex digest")
    if manifest.get("command_status") != "passed":
        errors.append("command_status must be 'passed'")
    if not isinstance(manifest.get("sample_size"), int) or manifest.get("sample_size", 0) <= 0:
        errors.append("sample_size must be a positive integer")
    metrics = manifest.get("metrics")
    if not isinstance(metrics, dict) or not metrics:
        errors.append("metrics must be a non-empty object")
    else:
        for name, value in metrics.items():
            if not isinstance(name, str) or _is_placeholder(name):
                errors.append("metric names must be non-placeholder strings")
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                errors.append(f"metric {name!r} must be a finite number")
    statistics = manifest.get("statistics")
    if not isinstance(statistics, dict):
        errors.append("statistics must be an object")
    else:
        numerator = statistics.get("numerator")
        denominator = statistics.get("denominator")
        if not isinstance(numerator, int) or numerator < 0:
            errors.append("statistics.numerator must be a non-negative integer")
        if not isinstance(denominator, int) or denominator <= 0:
            errors.append("statistics.denominator must be a positive integer")
        if isinstance(numerator, int) and isinstance(denominator, int) and numerator > denominator:
            errors.append("statistics.numerator cannot exceed denominator")
        if isinstance(denominator, int) and denominator != manifest.get("sample_size"):
            errors.append("statistics.denominator must equal sample_size")
        metric = statistics.get("metric")
        if not isinstance(metric, str) or _is_placeholder(metric):
            errors.append("statistics.metric must be a non-placeholder string")
        elif isinstance(metrics, dict) and metric not in metrics:
            errors.append("statistics.metric must name a reported metric")
        if not isinstance(statistics.get("confidence_method"), str) or not statistics.get(
            "confidence_method", ""
        ).strip():
            errors.append("statistics.confidence_method must be a non-empty string")
        elif _is_placeholder(statistics["confidence_method"]):
            errors.append("statistics.confidence_method contains a placeholder")
        if (
            isinstance(metric, str)
            and metric.endswith("_percent")
            and isinstance(metrics, dict)
            and isinstance(metrics.get(metric), (int, float))
            and not isinstance(metrics.get(metric), bool)
            and isinstance(numerator, int)
            and isinstance(denominator, int)
            and denominator > 0
            and abs(metrics[metric] - numerator / denominator * 100) > 0.01
        ):
            errors.append("reported percentage does not match statistics numerator/denominator")
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        errors.append("artifacts must be a non-empty array")
    else:
        resolved_base = base_dir.resolve() if base_dir else None
        artifact_roles = {}
        for index, artifact in enumerate(artifacts):
            if not isinstance(artifact, dict):
                errors.append(f"artifact {index} must be an object")
                continue
            relative_path = artifact.get("path")
            digest = artifact.get("sha256")
            role = artifact.get("role")
            if role not in REQUIRED_ARTIFACT_ROLES:
                errors.append(
                    f"artifact {index} role must be one of: {', '.join(sorted(REQUIRED_ARTIFACT_ROLES))}"
                )
            elif role in artifact_roles:
                errors.append(f"artifact role {role!r} must be unique")
            else:
                artifact_roles[role] = artifact
            if not isinstance(relative_path, str) or _is_placeholder(relative_path):
                errors.append(f"artifact {index} path must be a non-placeholder string")
                continue
            if not isinstance(digest, str) or not SHA256_PATTERN.fullmatch(digest.lower()):
                errors.append(f"artifact {index} sha256 must be a 64-character hex digest")
            if resolved_base:
                artifact_path = (resolved_base / relative_path).resolve()
                if resolved_base not in artifact_path.parents and artifact_path != resolved_base:
                    errors.append(f"artifact {index} path escapes the manifest directory")
                    continue
                if not artifact_path.is_file():
                    errors.append(f"artifact {index} does not exist: {relative_path}")
                    continue
                actual_digest = hashlib.sha256(artifact_path.read_bytes()).hexdigest()
                if isinstance(digest, str) and actual_digest != digest.lower():
                    errors.append(f"artifact {index} sha256 does not match file content")
                line_count = artifact.get("line_count")
                if line_count is not None:
                    actual_lines = len(artifact_path.read_text(encoding="utf-8").splitlines())
                    if line_count != actual_lines:
                        errors.append(f"artifact {index} line_count does not match file content")
                artifact["_resolved_path"] = artifact_path
        for role in sorted(REQUIRED_ARTIFACT_ROLES - artifact_roles.keys()):
            errors.append(f"missing artifact role: {role}")
        dataset_artifact = artifact_roles.get("dataset")
        if dataset_artifact:
            if dataset_artifact.get("sha256", "").lower() != str(dataset_hash).lower():
                errors.append("dataset_hash must match the dataset artifact sha256")
        if (
            resolved_base
            and manifest.get("module") == "foundations"
            and dataset_artifact
            and artifact_roles.get("run_records")
            and dataset_artifact.get("_resolved_path")
            and artifact_roles["run_records"].get("_resolved_path")
        ):
            _validate_foundations_records(
                manifest,
                dataset_artifact["_resolved_path"],
                artifact_roles["run_records"]["_resolved_path"],
                errors,
            )
    if not isinstance(manifest.get("failures"), list):
        errors.append("failures must be an array")
    protocol = manifest.get("protocol")
    if not isinstance(protocol, dict):
        errors.append("protocol must be an object")
    else:
        required_protocol = {
            "declared_before_run",
            "baseline",
            "candidate",
            "holdout_used_for_tuning",
            "confidence_method",
        }
        for field in sorted(required_protocol - protocol.keys()):
            errors.append(f"protocol missing field: {field}")
        if protocol.get("declared_before_run") is not True:
            errors.append("protocol.declared_before_run must be true")
        if not isinstance(protocol.get("holdout_used_for_tuning"), bool):
            errors.append("protocol.holdout_used_for_tuning must be boolean")
        elif protocol.get("holdout_used_for_tuning"):
            errors.append("protocol.holdout_used_for_tuning must be false for completion evidence")
        for field in ("baseline", "candidate", "confidence_method"):
            if not isinstance(protocol.get(field), str) or not protocol.get(field, "").strip():
                errors.append(f"protocol.{field} must be a non-empty string")
            elif _is_placeholder(protocol[field]):
                errors.append(f"protocol.{field} contains a placeholder")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate evidence for a declared course module.")
    parser.add_argument("--module", required=True, choices=sorted(KNOWN_MODULES))
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()
    path = args.manifest
    manifest = json.loads(path.read_text(encoding="utf-8"))
    errors = validate_manifest(manifest, path.parent, expected_module=args.module)
    if errors:
        raise SystemExit("\n".join(errors))
    print(f"valid evidence manifest: {path}")


if __name__ == "__main__":
    main()
