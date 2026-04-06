import ipaddress
import socket
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from app.core.exceptions import AppException

BLOCKED_HOSTS = {"localhost", "127.0.0.1", "0.0.0.0", "::1"}
ALLOWED_PORTS = {80, 443, 8080, 8443, None}
TRACKING_QUERY_PREFIXES = ("utm_", "ref", "source")


def _is_private_ip(hostname: str) -> bool:
    try:
        ip = ipaddress.ip_address(hostname)
        return ip.is_private or ip.is_loopback or ip.is_reserved or ip.is_link_local
    except ValueError:
        return False


def _resolve_private_hosts(hostname: str) -> bool:
    try:
        infos = socket.getaddrinfo(hostname, None)
    except socket.gaierror:
        return False
    for info in infos:
        address = info[4][0]
        if _is_private_ip(address):
            return True
    return False


def normalize_url(url: str) -> str:
    parsed = urlparse(url.strip())
    if parsed.scheme not in {"http", "https"}:
        raise AppException(400, "invalid_url", "URL must use http or https.")
    host = parsed.hostname.lower() if parsed.hostname else ""
    if not host:
        raise AppException(400, "invalid_url", "URL must include a hostname.")
    path = parsed.path or "/"
    if path != "/" and path.endswith("/"):
        path = path[:-1]
    filtered_query = [
        (key, value)
        for key, value in parse_qsl(parsed.query, keep_blank_values=False)
        if not any(key.lower().startswith(prefix) for prefix in TRACKING_QUERY_PREFIXES)
    ]
    normalized = parsed._replace(
        scheme=parsed.scheme.lower(),
        netloc=host if parsed.port in {80, 443, None} else f"{host}:{parsed.port}",
        path=path,
        params="",
        query=urlencode(filtered_query),
        fragment="",
    )
    return urlunparse(normalized)


def validate_safe_public_url(url: str, *, allow_private_network: bool = False) -> str:
    normalized = normalize_url(url)
    parsed = urlparse(normalized)
    host = parsed.hostname or ""
    if host.lower() in BLOCKED_HOSTS:
        raise AppException(400, "unsafe_url", "Private or local network targets are not allowed.")
    if parsed.port not in ALLOWED_PORTS:
        raise AppException(400, "unsafe_url", "Unsupported URL port.")
    if not allow_private_network:
        if _is_private_ip(host) or _resolve_private_hosts(host):
            raise AppException(400, "unsafe_url", "Private or local network targets are not allowed.")
    return normalized
