import json
import tempfile
import unittest
from pathlib import Path

from workbench.evidence import validate_manifest
from workbench.scaffold import MODULES, scaffold_module


class ScaffoldTests(unittest.TestCase):
    def test_every_later_module_creates_contract_fixture_and_schema(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for module_number, module in MODULES.items():
                scaffold_module(root, module_number)
                self.assertTrue((root / "src" / "workbench" / module.package / "contracts.py").is_file())
                self.assertTrue((root / module.test_path).is_file())
                self.assertTrue((root / module.cases_path).is_file())
                self.assertTrue(
                    (root / "schemas" / f"module-{module_number:02d}-evidence.schema.json").is_file()
                )
                schema = json.loads(
                    (root / "schemas" / f"module-{module_number:02d}-evidence.schema.json").read_text(
                        encoding="utf-8"
                    )
                )
                template = json.loads(
                    (root / "examples" / f"module-{module_number:02d}-evidence-template.json").read_text(
                        encoding="utf-8"
                    )
                )
                self.assertTrue(set(schema["required"]).issubset(template))
                self.assertEqual("object", schema["properties"]["protocol"]["type"])
                template_errors = validate_manifest(template, expected_module=module.module_id)
                self.assertIn("command_status must be 'passed'", template_errors)
                self.assertIn("sample_size must be a positive integer", template_errors)
                self.assertIn("metrics must be a non-empty object", template_errors)
                self.assertIn("dataset_hash contains a placeholder", template_errors)
                self.assertIn("artifact 1 path must be a non-placeholder string", template_errors)
                self.assertEqual("dataset", template["artifacts"][0]["role"])
                self.assertEqual("run_records", template["artifacts"][1]["role"])
                for command_module in module.command_modules:
                    self.assertTrue(
                        (root / "src" / "workbench" / module.package / f"{command_module}.py").is_file()
                    )

    def test_scaffolder_refuses_to_overwrite_learner_work(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            scaffold_module(root, 2)
            with self.assertRaises(FileExistsError):
                scaffold_module(root, 2)


if __name__ == "__main__":
    unittest.main()
