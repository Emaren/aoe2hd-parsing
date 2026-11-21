"""Regression tests for production admin-authentication fail-closed behavior.

Only the verification function is extracted from the route's Python AST so the
tests do not import database connections or require production secrets.
"""
import ast
import os
import secrets
import unittest
from pathlib import Path
from unittest.mock import patch


class AuthError(Exception):
    def __init__(self, status_code, detail):
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


def load_admin_check():
    route = Path(__file__).resolve().parents[1] / "routes" / "admin_routes_async.py"
    tree = ast.parse(route.read_text(encoding="utf-8"), filename=str(route))
    selected = next(
        node for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "verify_admin_token"
    )
    module = ast.fix_missing_locations(ast.Module(body=[selected], type_ignores=[]))
    namespace = {
        "Header": lambda default=None, alias=None: default,
        "HTTPException": AuthError,
        "os": os,
        "secrets": secrets,
    }
    exec(compile(module, str(route), "exec"), namespace)
    return namespace["verify_admin_token"]


class AdminAuthenticationTests(unittest.TestCase):
    def setUp(self):
        self.verify = load_admin_check()

    def test_missing_environment_rejects_even_with_a_presented_token(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(AuthError) as ctx:
                self.verify(authorization=None, x_admin_token="any-user-input")
            self.assertEqual(ctx.exception.status_code, 503)

    def test_empty_environment_rejects(self):
        with patch.dict(os.environ, {"ADMIN_TOKEN": "   "}, clear=True):
            with self.assertRaises(AuthError) as ctx:
                self.verify(authorization=None, x_admin_token="any-user-input")
            self.assertEqual(ctx.exception.status_code, 503)

    def test_exact_header_accepted_with_explicit_configuration(self):
        with patch.dict(os.environ, {"ADMIN_TOKEN": "private-test-fixture"}, clear=True):
            self.assertIsNone(self.verify(authorization=None, x_admin_token="private-test-fixture"))

    def test_bearer_authorization_accepted(self):
        with patch.dict(os.environ, {"ADMIN_TOKEN": "private-test-fixture"}, clear=True):
            self.assertIsNone(self.verify(authorization="Bearer private-test-fixture", x_admin_token=None))

    def test_wrong_header_rejected(self):
        with patch.dict(os.environ, {"ADMIN_TOKEN": "private-test-fixture"}, clear=True):
            with self.assertRaises(AuthError) as ctx:
                self.verify(authorization=None, x_admin_token="wrong")
            self.assertEqual(ctx.exception.status_code, 401)
            self.assertNotIn("private-test-fixture", ctx.exception.detail)

    def test_no_header_rejected(self):
        with patch.dict(os.environ, {"ADMIN_TOKEN": "private-test-fixture"}, clear=True):
            with self.assertRaises(AuthError) as ctx:
                self.verify(authorization=None, x_admin_token=None)
            self.assertEqual(ctx.exception.status_code, 401)

    def test_bare_authorization_does_not_count_as_bearer(self):
        with patch.dict(os.environ, {"ADMIN_TOKEN": "private-test-fixture"}, clear=True):
            with self.assertRaises(AuthError) as ctx:
                self.verify(authorization="private-test-fixture", x_admin_token=None)
            self.assertEqual(ctx.exception.status_code, 401)

    def test_overlong_header_rejected(self):
        with patch.dict(os.environ, {"ADMIN_TOKEN": "private-test-fixture"}, clear=True):
            with self.assertRaises(AuthError) as ctx:
                self.verify(authorization=None, x_admin_token="x" * 513)
            self.assertEqual(ctx.exception.status_code, 401)


    def test_all_admin_routes_require_auth_before_mutation(self):
        route = Path(__file__).resolve().parents[1] / "routes" / "admin_routes_async.py"
        tree = ast.parse(route.read_text(encoding="utf-8"), filename=str(route))
        handlers = []
        for node in tree.body:
            if not isinstance(node, ast.AsyncFunctionDef):
                continue
            decorated = any(
                isinstance(dec, ast.Call)
                and isinstance(dec.func, ast.Attribute)
                and isinstance(dec.func.value, ast.Name)
                and dec.func.value.id == "router"
                and dec.func.attr in {"get", "post", "put", "patch", "delete"}
                for dec in node.decorator_list
            )
            if decorated:
                handlers.append(node)
                self.assertTrue(node.body, node.name)
                first = node.body[0]
                self.assertIsInstance(first, ast.Expr, node.name)
                self.assertIsInstance(first.value, ast.Call, node.name)
                self.assertIsInstance(first.value.func, ast.Name, node.name)
                self.assertEqual(first.value.func.id, "verify_admin_token", node.name)
                parameters = {arg.arg for arg in node.args.args}
                self.assertTrue({"authorization", "x_admin_token"} <= parameters, node.name)
        self.assertGreaterEqual(len(handlers), 3, "Must inspect every admin handler")


if __name__ == "__main__":
    unittest.main()
