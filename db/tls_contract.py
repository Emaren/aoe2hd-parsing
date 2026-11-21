"""One TLS policy for parser runtime and Alembic database connections.

Credentials and URL details are never logged. A local loopback database may use
plain TCP for development; every remote PostgreSQL endpoint requires TLS with
certificate verification. This module never opens a connection.
"""
import ipaddress
import ssl
from urllib.parse import urlsplit


def _is_local_loopback(database_url: str) -> bool:
    try:
        parsed = urlsplit(database_url)
        if not parsed.scheme.startswith("postgresql") and parsed.scheme != "postgres":
            raise ValueError("Unsupported database URL scheme")
        hostname = parsed.hostname
        if not hostname:
            raise ValueError("Database URL must have an explicit host")
        if hostname.casefold() == "localhost":
            return True
        try:
            return ipaddress.ip_address(hostname).is_loopback
        except ValueError:
            return False
    except (ValueError, TypeError) as exc:
        raise RuntimeError("PARSER_DATABASE_URL_INVALID") from None


def asyncpg_connection_options(database_url: str) -> dict:
    if _is_local_loopback(database_url):
        return {}
    return {"ssl": ssl.create_default_context()}


def sync_postgres_connection_options(database_url: str) -> dict:
    if _is_local_loopback(database_url):
        return {}
    return {"sslmode": "verify-full"}
