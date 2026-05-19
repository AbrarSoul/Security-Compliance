from app.services.files.validator import sanitize_filename


def test_sanitize_filename_strips_path():
    assert sanitize_filename("../../etc/passwd") == "passwd"
    assert "/" not in sanitize_filename("folder/data.csv")


def test_sanitize_filename_fallback():
    assert sanitize_filename("...") == "upload"
