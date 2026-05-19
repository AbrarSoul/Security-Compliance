from app.services.files.metadata_extractor import (
    extract_csv_metadata,
    extract_json_metadata,
    extract_metadata,
    extract_txt_metadata,
)


def test_extract_csv_metadata():
    content = b"name,email\nAlice,alice@example.com\nBob,bob@example.com\n"
    result = extract_csv_metadata(content, preview_rows=10)
    assert result.row_count == 2
    assert result.column_count == 2
    assert len(result.schema_json) == 2
    assert result.preview_json[0]["name"] == "Alice"


def test_extract_json_array_metadata():
    content = b'[{"id": 1, "name": "A"}, {"id": 2, "name": "B"}]'
    result = extract_json_metadata(content, preview_rows=10)
    assert result.row_count == 2
    assert result.column_count == 2
    assert result.extra_json["structure"] == "array_of_objects"


def test_extract_txt_metadata():
    content = b"line one\nline two\n\nline four"
    result = extract_txt_metadata(content, preview_rows=10)
    assert result.row_count == 4
    assert result.extra_json["line_count"] == 4
    assert result.extra_json["non_empty_line_count"] == 3


def test_extract_metadata_dispatcher():
    meta = extract_metadata("csv", b"a,b\n1,2\n")
    assert meta.column_count == 2
