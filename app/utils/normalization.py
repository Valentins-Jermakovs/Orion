
# ==============================
# Library imports
# ==============================

import hashlib
import html
import re
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


# ==============================
# Encoding normalization
# ==============================

# Common markers that indicate incorrectly decoded UTF-8 text.
_MOJIBAKE_MARKERS = (
    "Ã",
    "Â",
    "â",
    "ðŸ",
    "ï»¿",
    "\ufffd",
)


def _mojibake_score(value: str) -> int:
    """Estimate whether text contains common encoding artefacts."""
    return sum(
        value.count(marker) * len(marker)
        for marker in _MOJIBAKE_MARKERS
    )


def _try_repair_piece(value: str) -> str | None:
    """Try to repair a text segment using common legacy encodings."""
    original_score = _mojibake_score(value)

    for encoding in ("cp1252", "latin-1"):
        try:
            candidate = value.encode(encoding).decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            continue

        if _mojibake_score(candidate) < original_score:
            return candidate

    return None


def _repair_piece(value: str) -> str:
    """Repair encoding artefacts without changing valid text unnecessarily."""
    candidate = _try_repair_piece(value)

    if candidate is not None:
        return candidate

    # Try repairing short sections around suspicious characters.
    for marker in _MOJIBAKE_MARKERS:
        search_position = 0

        while True:
            position = value.find(marker, search_position)

            if position == -1:
                break

            search_position = position + len(marker)
            best_match: tuple[int, int, str] | None = None

            for start in range(max(0, position - 4), position + 1):
                for end in range(
                    min(len(value), position + len(marker) + 8),
                    position + len(marker) - 1,
                    -1,
                ):
                    piece = value[start:end]
                    repaired = _try_repair_piece(piece)

                    if repaired is None:
                        continue

                    if (
                        best_match is None
                        or end - start > best_match[1] - best_match[0]
                    ):
                        best_match = (start, end, repaired)

            if best_match is not None:
                start, end, repaired = best_match
                value = value[:start] + repaired + value[end:]
                search_position = start + len(repaired)

    return value


def repair_mojibake(value: str | None) -> str | None:
    """Repair common UTF-8 text decoded with the wrong encoding."""
    if value is None:
        return None

    repaired = value

    # Multiple passes can fix text that was encoded incorrectly twice.
    for _ in range(2):
        if not any(
            marker in repaired
            for marker in _MOJIBAKE_MARKERS
        ):
            break

        candidate = _try_repair_piece(repaired)

        if candidate is not None:
            repaired = candidate
            continue

        # Repair individual text segments to preserve valid Unicode.
        repaired = re.sub(
            r"\S+",
            lambda match: _repair_piece(match.group(0)),
            repaired,
        )

    return repaired


# ==============================
# Text normalization
# ==============================

def normalize_text(value: str | None) -> str | None:
    """Repair encoding artefacts and normalize whitespace."""
    if value is None:
        return None

    normalized = repair_mojibake(value) or ""
    normalized = re.sub(r"\s+", " ", normalized).strip()

    return normalized or None


def normalize_description(value: str | None) -> str | None:
    """Convert an HTML description into readable plain text."""
    if value is None:
        return None

    description = repair_mojibake(value) or ""

    # Remove script and style contents before stripping HTML tags.
    description = re.sub(
        r"<(script|style)\b[^>]*>.*?</\1\s*>",
        "",
        description,
        flags=re.IGNORECASE | re.DOTALL,
    )

    # Preserve meaningful line breaks and list formatting.
    description = re.sub(
        r"<br\s*/?>",
        "\n",
        description,
        flags=re.IGNORECASE,
    )

    description = re.sub(
        r"<li\b[^>]*>",
        "• ",
        description,
        flags=re.IGNORECASE,
    )

    description = re.sub(
        r"</(?:p|div|li|h[1-6]|section|article|ul|ol|blockquote|tr)\s*>",
        "\n",
        description,
        flags=re.IGNORECASE,
    )

    # Remove remaining HTML tags.
    description = re.sub(r"<[^>]+>", "", description)

    # Decode entities such as &amp;, &nbsp;, and &#39;.
    description = html.unescape(description)
    description = repair_mojibake(description) or ""

    # Normalize spaces without removing meaningful line breaks.
    description = re.sub(r"[ \t\f\v]+", " ", description)
    description = re.sub(r" *\n *", "\n", description)
    description = re.sub(r"\n{3,}", "\n\n", description)

    return description.strip() or None


# ==============================
# URL normalization
# ==============================

def normalize_url(url: str) -> str:
    """Normalize an absolute URL before using it for deduplication."""
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

    # Remove common tracking parameters while preserving other parameters.
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


# ==============================
# Vacancy deduplication
# ==============================

def create_deduplication_key(
    source_id: str,
    original_url: str,
    external_id: str | None = None,
) -> str:
    """Create a stable hash for identifying a vacancy."""
    normalized_source = source_id.strip().lower()

    if not normalized_source:
        raise ValueError("Source ID cannot be empty.")

    # Prefer the source identifier when one is available.
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
