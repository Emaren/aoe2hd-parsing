"""Non-network regressions for parser PostgreSQL credential and TLS boundaries."""
import ast
import importlib.util
import pathlib
import ssl
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("parser_tls_contract", ROOT / "db" / "tls_contract.py")
tls = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tls)


class DatabaseTlsTests(unittest.TestCase):
    def test_remote_tls_requires_validated_certificates(self):
        args = tls.asyncpg_connection_options(
            "postgresql+asyncpg://limited:placeholder@database.example.net:5432/app"
        )
        context = args["ssl"]
        self.assertIsInstance(context, ssl.SSLContext)
        self.assertTrue(context.check_hostname)
        self.assertEqual(context.verify_mode, ssl.CERT_REQUIRED)

    def test_local_loopback_exception_is_narrow(self):
        for host in ("localhost", "127.0.0.1", "[::1]"):
            self.assertEqual(
                tls.asyncpg_connection_options(
                    f"postgresql+asyncpg://u:placeholder@{host}:5432/db"
                ), {}
            )

    def test_remote_private_address_is_still_tls_required(self):
        args = tls.asyncpg_connection_options(
            "postgresql+asyncpg://u:placeholder@10.0.2.3:5432/db"
        )
        self.assertIn("ssl", args)

    def test_credentials_containing_localhost_cannot_bypass_tls(self):
        args = tls.asyncpg_connection_options(
            "postgresql+asyncpg://localhost-in-password:placeholder@db.example.net/db"
        )
        self.assertIn("ssl", args)

    def test_sync_client_uses_full_certificate_verification(self):
        self.assertEqual(
            tls.sync_postgres_connection_options(
                "postgresql://u:placeholder@db.example.net/db"
            ), {"sslmode": "verify-full"}
        )

    def test_missing_host_fails_without_echoing_credential(self):
        with self.assertRaisesRegex(RuntimeError, "^PARSER_DATABASE_URL_INVALID$"):
            tls.asyncpg_connection_options("postgresql+asyncpg:///db")

    def test_invalid_scheme_fails_closed(self):
        with self.assertRaisesRegex(RuntimeError, "^PARSER_DATABASE_URL_INVALID$"):
            tls.asyncpg_connection_options("sqlite:///data.sqlite")

    def test_migrations_and_runtime_both_use_tls_contract(self):
        migrations = (ROOT / "migrations" / "env.py").read_text()
        runtime = (ROOT / "db" / "db.py").read_text()
        ast.parse(migrations)
        ast.parse(runtime)
        self.assertIn("connect_args=asyncpg_connection_options(DB_URL)", migrations)
        self.assertIn("connect_args=sync_postgres_connection_options(DB_URL)", migrations)
        self.assertIn("connect_args = asyncpg_connection_options(DATABASE_URL)", runtime)
        self.assertNotIn('config.set_main_option("sqlalchemy.url", DB_URL)', migrations)

    def test_production_db_startup_never_implicitly_creates_tables(self):
        runtime = (ROOT / "db" / "db.py").read_text()
        self.assertIn('await conn.execute(text("SELECT 1"))', runtime)
        self.assertNotIn("Base.metadata.create_all", runtime)
        self.assertIn("reviewed alembic migrations", runtime.casefold())
        self.assertIn("PARSER_DATABASE_URL_REQUIRED", runtime)


if __name__ == "__main__":
    unittest.main()
