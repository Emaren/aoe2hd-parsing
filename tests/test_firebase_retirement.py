"""Static independent contract checks for retirement of legacy Firebase auth.

Never accepts a Firebase token, assumes a Firebase UID is a site-session UID,
executes network calls, or touches stored identities.
"""
import ast
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


def content(path):
    return (ROOT / path).read_text(encoding="utf-8")


class FirebaseRetirementContract(unittest.TestCase):
    def test_active_app_import_graph_contains_no_firebase(self):
        files = (
            "app.py",
            "routes/user_routes_async.py",
            "routes/user_me.py",
            "routes/user_register.py",
            "routes/user_ping.py",
            "routes/replay_routes_async.py",
            "routes/traffic_route.py",
        )
        for file in files:
            with self.subTest(file=file):
                tree = ast.parse(content(file))
                imports = [
                    alias.name
                    for node in ast.walk(tree)
                    if isinstance(node, ast.Import)
                    for alias in node.names
                ]
                imports.extend(
                    node.module or ""
                    for node in ast.walk(tree)
                    if isinstance(node, ast.ImportFrom)
                )
                self.assertFalse(
                    any("firebase" in item.casefold() for item in imports),
                    file,
                )

    def test_startup_cannot_create_firebase_app(self):
        app = content("app.py")
        self.assertNotIn("initialize_firebase", app)
        self.assertNotIn("firebase_admin", app)
        self.assertIn("await init_db_async()", app)

    def test_legacy_uid_writes_are_not_executable(self):
        tree = ast.parse(content("routes/user_routes_async.py"))
        funcs = {
            node.name: node
            for node in tree.body
            if isinstance(node, ast.AsyncFunctionDef)
        }
        for function in ("legacy_signup_retired", "legacy_name_change_retired",
                         "legacy_wallet_change_retired"):
            self.assertIn(function, funcs)
            body = ast.unparse(funcs[function])
            self.assertIn("legacy_identity_retired()", body)
            self.assertNotIn("db.commit", body)
        self.assertIn("HTTP_410_GONE", content("routes/user_routes_async.py"))

    def test_legacy_auth_dependency_fails_closed(self):
        module = ast.parse(content("routes/user_me.py"))
        fn = next(node for node in module.body
                  if isinstance(node, ast.AsyncFunctionDef)
                  and node.name == "get_current_user")
        body = ast.unparse(fn)
        self.assertIn("raise HTTPException", body)
        self.assertIn("HTTP_410_GONE", body)
        self.assertNotIn("verify_id_token", body)
        self.assertNotIn("SESSION_SECRET", body)

    def test_traffic_has_admin_gate_no_firebase_or_ip_leak(self):
        source = content("routes/traffic_route.py")
        self.assertIn("verify_admin_token(authorization, x_admin_token)", source)
        self.assertNotIn("auth.list_users", source)
        self.assertNotIn("ip_counts", source)
        self.assertNotIn("save_json", source)
        self.assertIn('"firebase_total": None', source)
        self.assertIn('"mismatch_count": None', source)
        self.assertIn('"traffic_log": None', source)

    def test_no_firebase_runtime_package(self):
        requirements = content("requirements.txt").casefold()
        self.assertNotIn("firebase-admin", requirements)

    def test_old_identity_script_and_key_excluded_from_image(self):
        dockerignore = content(".dockerignore")
        for forbidden in (
            ".env.*", "serviceAccountKey.json", "sync_firebase_users.py",
            "firebase_utils.py", "utils/auth_utils.py",
            "scripts/delete_firebase_users.py",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertIn(forbidden, dockerignore)

    def test_no_unreviewed_migrations_during_http_boot(self):
        dockerfile = content("Dockerfile")
        self.assertNotIn("alembic upgrade head &&", dockerfile)
        self.assertIn("exec uvicorn app:app", dockerfile)

    def test_live_database_uid_schema_is_not_rekeyed(self):
        user_model = content("db/models/user.py")
        self.assertIn('Column(String(100), unique=True, nullable=False)', user_model)
        self.assertNotIn("firebase_uid_to_site_uid", content("app.py"))
        self.assertNotIn("auth.verify_id_token", content("app.py"))


    def test_delete_all_is_permanently_retired(self):
        debug = content("routes/debug_routes_async.py")
        self.assertIn('async def delete_all():', debug)
        self.assertIn('raise HTTPException(status_code=410', debug)
        self.assertNotIn("delete(GameStats)", debug)
        self.assertNotIn("delete(User)", debug)
        self.assertNotIn("ENABLE_DEV_ENDPOINTS", debug)

    def test_legacy_betting_has_no_financial_mutation_authority(self):
        source = content("routes/bets.py")
        self.assertIn("Legacy demo betting disabled", source)
        self.assertNotIn("bets = {}", source)
        self.assertNotIn('"Bet accepted!"', source)
        self.assertNotIn('"Bet created!"', source)
        self.assertIn("_financial_unavailable()", source)

    def test_old_writers_retain_a_fail_closed_dependency(self):
        for file in ("routes/user_register.py", "routes/user_ping.py",
                     "routes/replay_routes_async.py"):
            with self.subTest(file=file):
                source = content(file)
                self.assertIn("from routes.user_me import get_current_user", source)
                self.assertIn("Depends(get_current_user)", source)


if __name__ == "__main__":
    unittest.main()
