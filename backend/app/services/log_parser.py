import re
from collections import Counter
from typing import Any


LEVEL_PATTERN = re.compile(
    r"\b(CRITICAL|FATAL|ERROR|WARN|WARNING|INFO|DEBUG)\b",
    re.IGNORECASE,
)

LEVEL_NORMALIZATION = {
    "FATAL": "CRITICAL",
    "WARN": "WARNING",
}

HTTP_STATUS_PATTERN = re.compile(
    r'"(?:[^"]*)" (?P<status>[1-5]\d{2})(?:\s|$)'
)


def determine_severity(
    level_counts: dict[str, int],
    http_client_error_count: int,
    http_server_error_count: int,
) -> dict[str, str]:
    critical_count = level_counts.get("CRITICAL", 0)
    error_count = level_counts.get("ERROR", 0)

    if critical_count > 0:
        severity = "CRITICAL"
        priority = "Immediate investigation"

    elif http_server_error_count > 0 or error_count >= 3:
        severity = "HIGH"
        priority = "Investigate promptly"

    elif error_count > 0 or http_client_error_count > 0:
        severity = "MEDIUM"
        priority = "Review and investigate"

    else:
        severity = "LOW"
        priority = "Routine monitoring"

    return {
        "overall_severity": severity,
        "investigation_priority": priority,
    }


def parse_log(content: str) -> dict[str, Any]:
    level_counts: Counter[str] = Counter()
    error_lines: Counter[str] = Counter()
    http_status_counts: Counter[str] = Counter()
    total_lines = 0

    for line in content.splitlines():
        line = line.strip()

        if not line:
            continue

        total_lines += 1

        # Detect explicit application-log severity labels.
        match = LEVEL_PATTERN.search(line)

        if match:
            level = match.group(1).upper()
            level = LEVEL_NORMALIZATION.get(level, level)
            level_counts[level] += 1

            if level in {"ERROR", "CRITICAL"}:
                error_lines[line] += 1

        # Independently detect HTTP access-log status codes.
        status_match = HTTP_STATUS_PATTERN.search(line)

        if status_match:
            status = status_match.group("status")
            http_status_counts[status] += 1

    client_errors = sum(
        count
        for status, count in http_status_counts.items()
        if status.startswith("4")
    )

    server_errors = sum(
        count
        for status, count in http_status_counts.items()
        if status.startswith("5")
    )

    error_count = level_counts["ERROR"] + level_counts["CRITICAL"]

    severity_summary = determine_severity(
        level_counts=dict(level_counts),
        http_client_error_count=client_errors,
        http_server_error_count=server_errors,
    )

    return {
        "total_lines": total_lines,
        "level_counts": dict(level_counts),
        "error_count": error_count,
        "top_errors": [
            {"message": message, "count": count}
            for message, count in error_lines.most_common(5)
        ],
        "http_status_counts": dict(http_status_counts),
        "http_client_error_count": client_errors,
        "http_server_error_count": server_errors,
        **severity_summary,
    }
