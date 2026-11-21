"""Isolated execution tests for the actual async FastAPI startup DB check.

No production DB, credentials, migrations, or network connections are required.
We compile only the merged startup function and replace its dependencies with
tiny in-memory fakes, so these assertions test real source control flow.
"""
import ast
import pathlib
import types
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


class ConnectionDropped(Exception):
    pass


class OtherConnectionFailure(Exception):
    pass


class FakeConnection:
    def __init__(self, attempts, outcomes, statements):
        self.attempts = attempts
        self.outcomes = outcomes
        self.statements = statements

    async def __aenter__(self):
        self.attempts.append("attempt")
        index = len(self.attempts) - 1
        if index < len(self.outcomes) and self.outcomes[index] is not None:
            raise self.outcomes[index]
        return self

    async def __aexit__(self, *args):
        return False

    async def execute(self, statement):
        self.statements.append(statement)


class FakeEngine:
    def __init__(self, attempts, outcomes, statements):
        self.attempts = attempts
        self.outcomes = outcomes
        self.statements = statements

    def begin(self):
        return FakeConnection(self.attempts, self.outcomes, self.statements)


def executable_startup(outcomes):
    path = ROOT / "db" / "db.py"
    source = path.read_text(encoding="utf-8")
    module = ast.parse(source, filename=str(path))
    func = next(
        node for node in module.body
        if isinstance(node, ast.AsyncFunctionDef) and node.name == "init_db_async"
    )
    body = ast.fix_missing_locations(ast.Module(body=[func], type_ignores=[]))
    attempts, sleeps, statements, logs = [], [], [], []

    async def fake_sleep(seconds):
        sleeps.append(seconds)

    namespace = {
        "engine": FakeEngine(attempts, outcomes, statements),
        "text": lambda sql: sql,
        "asyncio": types.SimpleNamespace(sleep=fake_sleep),
        "asyncpg": types.SimpleNamespace(
            exceptions=types.SimpleNamespace(ConnectionDoesNotExistError=ConnectionDropped)
        ),
        "logging": types.SimpleNamespace(
            info=lambda *args: logs.append(("info", args)),
            warning=lambda *args: logs.append(("warning", args)),
            error=lambda *args: logs.append(("error", args)),
        ),
        "RuntimeError": RuntimeError,
        "range": range,
        "type": type,
    }
    exec(compile(body, str(path), "exec"), namespace)
    return namespace["init_db_async"], attempts, sleeps, statements, logs, source


class DatabaseStartupRetryContractTests(unittest.IsolatedAsyncioTestCase):
    async def test_success_on_first_attempt(self):
        startup, attempts, sleeps, sql, logs, _ = executable_startup([])
        self.assertIsNone(await startup())
        self.assertEqual(len(attempts), 1)
        self.assertEqual(sleeps, [])
        self.assertEqual(sql, ["SELECT 1"])
        self.assertEqual([level for level, _ in logs if level == "info"], ["info"])

    async def test_transient_disconnect_then_recovery(self):
        startup, attempts, sleeps, sql, _, _ = executable_startup(
            [ConnectionDropped("injected"), ConnectionDropped("injected"), None]
        )
        self.assertIsNone(await startup())
        self.assertEqual(len(attempts), 3)
        self.assertEqual(sleeps, [2, 2])
        self.assertEqual(sql, ["SELECT 1"])

    async def test_exhaustion_never_masquerades_as_success(self):
        startup, attempts, sleeps, sql, logs, _ = executable_startup(
            [ConnectionDropped("SECRET_CANARY_DO_NOT_LOG")] * 5
        )
        with self.assertRaisesRegex(
            RuntimeError, "^PARSER_DB_STARTUP_RETRIES_EXHAUSTED$"
        ) as ctx:
            await startup()
        self.assertTrue(ctx.exception.__suppress_context__)
        self.assertEqual(len(attempts), 5)
        self.assertEqual(sleeps, [2, 2, 2, 2])
        self.assertEqual(sql, [])
        self.assertFalse(any(level == "info" for level, _ in logs))
        self.assertNotIn("SECRET_CANARY", repr(logs))

    async def test_unexpected_connection_error_fails_immediately(self):
        startup, attempts, sleeps, sql, logs, _ = executable_startup(
            [OtherConnectionFailure("secret-provider-message")]
        )
        with self.assertRaises(OtherConnectionFailure):
            await startup()
        self.assertEqual(len(attempts), 1)
        self.assertEqual(sleeps, [])
        self.assertEqual(sql, [])
        self.assertEqual(len([x for x in logs if x[0] == "error"]), 1)
        self.assertNotIn("secret-provider-message", repr(logs))

    async def test_no_schema_migrations_or_ddl_at_startup(self):
        _, _, _, _, _, source = executable_startup([])
        self.assertIn('text("SELECT 1")', source)
        self.assertNotIn("Base.metadata.create_all", source)
        self.assertNotIn("alembic upgrade", source)
        self.assertNotIn("DROP TABLE", source)


if __name__ == "__main__":
    unittest.main()
