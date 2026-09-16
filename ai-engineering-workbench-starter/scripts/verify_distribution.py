from __future__ import annotations

import argparse
import hashlib
import zipfile
from pathlib import Path


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def source_files(root: Path) -> dict[str, str]:
    files: dict[str, str] = {}
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(root)
        if "__pycache__" in relative.parts or relative.suffix == ".pyc" or relative.parts[0] == "artifacts":
            continue
        files[relative.as_posix()] = sha256_bytes(path.read_bytes())
    return files


def archive_files(path: Path) -> dict[str, str]:
    with zipfile.ZipFile(path) as archive:
        return {
            entry.filename.replace("\\", "/"): sha256_bytes(archive.read(entry))
            for entry in archive.infolist()
            if not entry.is_dir()
        }


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify that the downloadable starter ZIP matches source.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--zip", dest="zip_path", type=Path)
    args = parser.parse_args()

    root = args.root.resolve()
    zip_path = args.zip_path.resolve() if args.zip_path else root.with_suffix(".zip")
    expected = source_files(root)
    actual = archive_files(zip_path)
    if expected != actual:
        missing = sorted(expected.keys() - actual.keys())
        extra = sorted(actual.keys() - expected.keys())
        changed = sorted(name for name in expected.keys() & actual.keys() if expected[name] != actual[name])
        raise SystemExit(f"distribution mismatch: missing={missing}, extra={extra}, changed={changed}")
    print(f"distribution verified: {len(expected)} files match {zip_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
