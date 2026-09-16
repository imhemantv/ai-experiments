import json
from dataclasses import asdict
from pathlib import Path

from workbench.contracts import ModelRequest, ModelResult


def append_run(path: Path, request: ModelRequest, result: ModelResult) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    record = {"request": asdict(request), "result": asdict(result)}
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(record, ensure_ascii=True) + "\n")
