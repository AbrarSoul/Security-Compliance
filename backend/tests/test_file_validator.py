import io

import pytest
from docx import Document
from reportlab.pdfgen import canvas

from app.services.files.metadata_extractor import extract_metadata
from app.services.files.file_validation import (
    extension_from_name,
    sanitize_filename,
    unsupported_file_type_response,
    validate_file_magic,
)
from app.services.scanner.dataset_loader import load_dataset_columns


def test_sanitize_filename_strips_path():
    assert sanitize_filename("../../etc/passwd") == "passwd"
    assert "/" not in sanitize_filename("folder/data.csv")


def test_sanitize_filename_fallback():
    assert sanitize_filename("...") == "upload"


def test_unsupported_extension_response():
    resp = unsupported_file_type_response()
    assert resp["error"] == "Unsupported file type"
    assert "CSV" in resp["supported_file_types"]
    assert "XLSX" in resp["supported_file_types"]


def test_extension_from_name_rejects_unknown():
    assert extension_from_name("data.exe") is None
    assert extension_from_name("data.csv") == "csv"


def test_validate_tsv_magic():
    validate_file_magic("tsv", b"name\temail\nAlice\talice@example.com\n")


def test_validate_jsonl_magic():
    validate_file_magic("jsonl", b'{"name": "Alice"}\n{"name": "Bob"}\n')


def test_validate_xml_magic():
    content = b'<?xml version="1.0"?><records><item><name>Alice</name></item></records>'
    validate_file_magic("xml", content)


def test_validate_yaml_magic():
    validate_file_magic("yaml", b"name: Alice\nemail: alice@example.com\n")


def test_extract_tsv_metadata():
    content = b"name\temail\nAlice\talice@example.com\nBob\tbob@example.com\n"
    meta = extract_metadata("tsv", content)
    assert meta.row_count == 2
    assert meta.column_count == 2


def test_extract_jsonl_metadata():
    content = b'{"email": "a@example.com"}\n{"email": "b@example.com"}\n'
    meta = extract_metadata("jsonl", content)
    assert meta.row_count == 2
    assert meta.column_count == 1


def test_extract_xml_metadata():
    content = b"""<records>
      <item><name>Alice</name><email>alice@example.com</email></item>
      <item><name>Bob</name><email>bob@example.com</email></item>
    </records>"""
    meta = extract_metadata("xml", content)
    assert meta.row_count == 2
    assert meta.column_count == 2


def test_extract_yaml_metadata():
    content = b"- name: Alice\n  email: alice@example.com\n- name: Bob\n  email: bob@example.com\n"
    meta = extract_metadata("yaml", content)
    assert meta.row_count == 2
    assert meta.column_count == 2


def test_load_dataset_columns_tsv():
    content = b"email\nalice@example.com\n"
    columns = load_dataset_columns("tsv", content)
    assert any(col.name == "email" for col in columns)


def test_load_dataset_columns_log():
    content = b"2024-01-01 INFO user login\n2024-01-02 ERROR failed\n"
    columns = load_dataset_columns("log", content)
    assert columns[0].name == "line"
    assert len(columns[0].cells) == 2


def test_validate_jsonl_rejects_invalid_line():
    with pytest.raises(Exception):
        validate_file_magic("jsonl", b"not json\n")


def _sample_pdf(content: str = "Contact: alice@example.com") -> bytes:
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer)
    pdf.drawString(72, 720, content)
    pdf.save()
    return buffer.getvalue()


def _sample_docx(content: str = "Contact: alice@example.com") -> bytes:
    buffer = io.BytesIO()
    document = Document()
    document.add_paragraph(content)
    document.save(buffer)
    return buffer.getvalue()


def test_validate_pdf_magic():
    validate_file_magic("pdf", _sample_pdf())


def test_validate_docx_magic():
    validate_file_magic("docx", _sample_docx())


def test_extract_pdf_metadata():
    meta = extract_metadata("pdf", _sample_pdf("Line one\nLine two"))
    assert meta.row_count >= 1
    assert meta.extra_json["format"] == "pdf"
    assert meta.extra_json["page_count"] == 1


def test_extract_docx_metadata():
    meta = extract_metadata("docx", _sample_docx("alice@example.com"))
    assert meta.row_count == 1
    assert meta.extra_json["format"] == "docx"


def test_load_dataset_columns_pdf():
    columns = load_dataset_columns("pdf", _sample_pdf("alice@example.com"))
    assert columns[0].name == "line"
    assert len(columns[0].cells) >= 1


def _sample_xlsx(rows: list[list[str]] | None = None) -> bytes:
    from app.services.files.excel_io import build_sample_xlsx

    if rows is None:
        rows = [["email", "name"], ["alice@example.com", "Alice"]]
    return build_sample_xlsx(rows)


def test_validate_xlsx_magic():
    validate_file_magic("xlsx", _sample_xlsx())


def test_extract_xlsx_metadata():
    meta = extract_metadata("xlsx", _sample_xlsx())
    assert meta.row_count == 1
    assert meta.column_count == 2
    assert meta.extra_json["format"] == "xlsx"
    assert meta.extra_json["sheet_count"] == 1


def test_load_dataset_columns_xlsx():
    columns = load_dataset_columns("xlsx", _sample_xlsx())
    assert any(col.name == "email" for col in columns)
    assert columns[0].cells[0].value == "alice@example.com"

