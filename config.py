import json
import os
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
env_loaded = False

# Get ENV early
ENV = os.getenv("ENV", os.getenv("RENDER", False) and "production" or "development")

# ✅ 1. Prefer .env.override only in development
override_path = os.path.join(BASE_DIR, ".env.override")
if ENV != "production" and os.path.exists(override_path):
    load_dotenv(dotenv_path=override_path)
    env_loaded = True
    print("✅ Loaded override from .env.override (dev only)")

# ✅ 2. Load env-specific file (production/dev/etc)
if not env_loaded:
    env_file = (
        ".env.production" if ENV == "production"
        else ".env.dev" if ENV == "dev"
        else ".env.fastdev" if ENV == "fastdev"
        else ".env"
    )
    env_path = os.path.join(BASE_DIR, env_file)
    if os.path.exists(env_path):
        load_dotenv(dotenv_path=env_path)
        env_loaded = True
        print(f"✅ Loaded environment: {ENV} from {env_file}")
    else:
        print(f"⚠️ No env file found for {ENV}. Proceeding with defaults.")

# ✅ 3. Load .env.local last, but only in dev mode
local_path = os.path.join(BASE_DIR, ".env.local")
if ENV == "development" and os.path.exists(local_path):
    load_dotenv(dotenv_path=local_path, override=True)
    print("✅ Loaded .env.local (final override layer for dev)")

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
print(f"🚀 ENV is: {ENV}")
print(f"🌐 FASTAPI_API_URL is: {os.getenv('FASTAPI_API_URL')}")
print("🐘 DATABASE_URL configured:", bool(os.getenv("DATABASE_URL")))
