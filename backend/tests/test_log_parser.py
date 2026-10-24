
from app.services.log_parser import parse_log


def test_parse_log_counts_severity_levels():
    content = """
    INFO Application started
    WARNING Disk usage is high
    ERROR Database connection failed
    CRITICAL Service unavailable
    """

    result = parse_log(content)

    assert result["total_lines"] == 4
    assert result["level_counts"]["INFO"] == 1
    assert result["level_counts"]["WARNING"] == 1
    assert result["level_counts"]["ERROR"] == 1
    assert result["level_counts"]["CRITICAL"] == 1
    assert result["error_count"] == 2


def test_parse_log_normalizes_warn_and_fatal():
    content = "WARN High latency\nFATAL Process crashed"

    result = parse_log(content)

    assert result["level_counts"]["WARNING"] == 1
    assert result["level_counts"]["CRITICAL"] == 1


def test_parse_log_handles_empty_content():
    result = parse_log("")

    assert result["total_lines"] == 0
    assert result["level_counts"] == {}
    assert result["error_count"] == 0
    assert result["top_errors"] == []


def test_parse_log_analyzes_http_access_logs():
    content = (
        '127.0.0.1 - - [24/Oct/2026:15:24:01 +0530] '
        '"GET /index.html HTTP/1.1" 200 2326\n'
        '10.0.0.4 - - [24/Oct/2026:15:24:10 +0530] '
        '"GET /assets/style.css HTTP/1.1" 304 0\n'
        '198.51.100.42 - - [24/Oct/2026:15:24:22 +0530] '
        '"GET /admin HTTP/1.1" 404 196\n'
        '203.0.113.88 - - [24/Oct/2026:15:24:25 +0530] '
        '"GET /api HTTP/1.1" 500 50\n'
    )

    result = parse_log(content)

    assert result["total_lines"] == 4
    assert result["http_status_counts"] == {
        "200": 1,
        "304": 1,
        "404": 1,
        "500": 1,
    }
    assert result["http_client_error_count"] == 1
    assert result["http_server_error_count"] == 1
    assert result["error_count"] == 0


def test_parse_log_assigns_critical_severity():
    result = parse_log("CRITICAL Service unavailable")

    assert result["overall_severity"] == "CRITICAL"
    assert result["investigation_priority"] == "Immediate investigation"


def test_parse_log_assigns_high_severity_for_http_server_error():
    content = '"GET /api HTTP/1.1" 500 50'

    result = parse_log(content)

    assert result["http_server_error_count"] == 1
    assert result["overall_severity"] == "HIGH"
    assert result["investigation_priority"] == "Investigate promptly"


def test_parse_log_assigns_medium_severity_for_http_client_error():
    content = '"GET /admin HTTP/1.1" 404 196'

    result = parse_log(content)

    assert result["overall_severity"] == "MEDIUM"
    assert result["investigation_priority"] == "Review and investigate"


def test_parse_log_assigns_low_severity_without_detected_issues():
    result = parse_log("INFO Application started")

    assert result["overall_severity"] == "LOW"
    assert result["investigation_priority"] == "Routine monitoring"
