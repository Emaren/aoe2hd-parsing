import json
import os
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Production and CI NEVER load committed dotenv files; injected environment
# variables are the only credential authority. Even a developer's production
# ENV flag must not select the historically tracked .env.production.
ENV = (os.getenv("ENV") or ("production" if os.getenv("RENDER_SERVICE_ID") else "development")).casefold()
is_managed_runtime = bool(os.getenv("RENDER_SERVICE_ID") or os.getenv("RENDER"))
allow_dev_dotenv = (
    os.getenv("PARSER_ALLOW_LOCAL_DOTENV") == "true"
    and ENV in {"development", "dev", "fastdev", "test"}
    and not is_managed_runtime
)
if allow_dev_dotenv:
    from dotenv import load_dotenv
    # Deliberate local-only opt-in; no .env.production or .env.render fallback.
    for name in (".env.override", ".env.dev", ".env.fastdev", ".env.local", ".env"):
        path = os.path.join(BASE_DIR, name)
        if os.path.isfile(path):
            load_dotenv(dotenv_path=path, override=False)

# --- Exports ---
def get_fastapi_api_url():
    return os.getenv("FASTAPI_API_URL", "http://localhost:8002/api/parse_replay")

def get_api_targets():
    val = os.getenv("API_TARGETS")
    if val:
        return [x.strip() for x in val.split(",")]
    return []

def load_config():
    config_path = os.path.join(BASE_DIR, "config.json")
    if not os.path.exists(config_path):
        raise RuntimeError(f"❌ Configuration file not found at {config_path}")
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"❌ JSON error in config.json: {e}")
    except Exception as e:
        raise RuntimeError(f"❌ Failed to load config.json: {e}")

# ✅ Debug print
print("PARSER_RUNTIME_CONFIG_INJECTED_ONLY", not allow_dev_dotenv)
print("PARSER_DATABASE_URL_CONFIGURED", bool(os.getenv("DATABASE_URL")))
