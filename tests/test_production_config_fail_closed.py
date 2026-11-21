"""Production must never resurrect admin/database secrets from tracked dotenv files."""
import os
import pathlib
import runpy
import sys
import types
import unittest
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parents[1]


class RuntimeConfigSecurityTests(unittest.TestCase):
    def run_configuration(self, extra):
        attempted_loads = []
        fake_dotenv = types.ModuleType("dotenv")
        fake_dotenv.load_dotenv = lambda *args, **kwargs: attempted_loads.append(
            pathlib.Path(kwargs.get("dotenv_path", "")).name
        )
        environment = {"ENV": "production", **extra}
        with patch.dict(os.environ, environment, clear=True):
            with patch.dict(sys.modules, {"dotenv": fake_dotenv}):
                result = runpy.run_path(str(ROOT / "config.py"))
                admin_configured = "ADMIN_TOKEN" in os.environ
        return attempted_loads, admin_configured, result["allow_dev_dotenv"]

    def test_missing_production_admin_token_never_falls_back_to_repo(self):
        loaded, admin, opt_in = self.run_configuration({})
        self.assertEqual(loaded, [])
        self.assertFalse(admin)
        self.assertFalse(opt_in)

    def test_production_rejects_even_explicit_dev_opt_in(self):
        loaded, admin, opt_in = self.run_configuration(
            {"PARSER_ALLOW_LOCAL_DOTENV": "true"}
        )
        self.assertEqual(loaded, [])
        self.assertFalse(admin)
        self.assertFalse(opt_in)

    def test_render_runtime_cannot_opt_into_dev_dotenv(self):
        loaded, admin, opt_in = self.run_configuration({
            "ENV": "development", "RENDER_SERVICE_ID": "srv-synthetic",
            "PARSER_ALLOW_LOCAL_DOTENV": "true",
        })
        self.assertEqual(loaded, [])
        self.assertFalse(admin)
        self.assertFalse(opt_in)

    def test_default_development_does_not_load_files(self):
        loaded, admin, opt_in = self.run_configuration({"ENV": "development"})
        self.assertEqual(loaded, [])
        self.assertFalse(admin)
        self.assertFalse(opt_in)

    def test_dev_opt_in_never_reads_production_or_render_dotenv(self):
        loaded, _, opt_in = self.run_configuration({
            "ENV": "development", "PARSER_ALLOW_LOCAL_DOTENV": "true"
        })
        self.assertTrue(opt_in)
        self.assertNotIn(".env.production", loaded)
        self.assertNotIn(".env.render", loaded)


if __name__ == "__main__":
    unittest.main()
