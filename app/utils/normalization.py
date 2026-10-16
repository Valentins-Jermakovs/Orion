
import hashlib
import re
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


def normalize_text(value: str | None) -> str | None:
    """Remove unnecessary whitespace from text."""
    if value is None:
        return None

    normalized = re.sub(r"\s+", " ", value).strip()

    return normalized or None


def normalize_url(url: str) -> str:
    """Normalize a URL before using it for deduplication."""
    parts = urlsplit(url.strip())

    scheme = parts.scheme.lower()
    hostname = (parts.hostname or "").lower()

    if not scheme or not hostname:
        raise ValueError("A valid absolute URL is required.")

    # Remove default ports from the URL.
    port = parts.port

    if port is not None and not (
        (scheme == "http" and port == 80)
        or (scheme == "https" and port == 443)
    ):
        hostname = f"{hostname}:{port}"

    path = parts.path.rstrip("/") or "/"

    # Remove common tracking parameters but preserve other query parameters.
    tracking_parameters = {
        "fbclid",
        "gclid",
        "mc_cid",
        "mc_eid",
    }

    query_parameters = [
        (key, value)
        for key, value in parse_qsl(
            parts.query,
            keep_blank_values=True,
        )
        if key.lower() not in tracking_parameters
        and not key.lower().startswith("utm_")
    ]

    normalized_query = urlencode(sorted(query_parameters))

    return urlunsplit(
        (
            scheme,
            hostname,
            path,
            normalized_query,
            "",
        )
    )


def create_deduplication_key(
    source_id: str,
    original_url: str,
    external_id: str | None = None,
) -> str:
    """Create a stable key for identifying a vacancy."""
    normalized_source = source_id.strip().lower()

    if not normalized_source:
        raise ValueError("Source ID cannot be empty.")

    if external_id and external_id.strip():
        unique_value = (
            f"{normalized_source}:id:{external_id.strip()}"
        )
    else:
        normalized_original_url = normalize_url(original_url)
        unique_value = (
            f"{normalized_source}:url:{normalized_original_url}"
        )

    return hashlib.sha256(
        unique_value.encode("utf-8")
    ).hexdigest()
