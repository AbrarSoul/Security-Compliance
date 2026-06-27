from app.services.reports.summary_text import format_location_list, format_issue_summary


def test_format_location_list_with_extra():
    evidence = {
        "location_type": "row",
        "locations": [{"index": 2, "preview": "al***"}, {"index": 5, "preview": "bo***"}],
        "additional_match_count": 3,
    }
    assert format_location_list(evidence) == "Rows 2, 5 (+3 more)"


def test_format_location_list_records():
    evidence = {
        "location_type": "record",
        "locations": [{"index": 1, "preview": "a@b.com"}],
    }
    assert format_location_list(evidence) == "Record 1"


def test_format_issue_summary_includes_locations():
    issue = {
        "type": "email",
        "column": "email",
        "match_rate": 0.5,
        "evidence": {
            "location_type": "row",
            "locations": [{"index": 3, "preview": "al***@example.com"}],
        },
    }
    summary = format_issue_summary(issue)
    assert "email addresses" in summary
    assert "column 'email'" in summary
    assert "Row 3" in summary
