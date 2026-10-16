MAX_SEASON_RULES_DOCUMENT_BYTES = 10 * 1024 * 1024  # 10MB

SEASON_RULES_DOCUMENT_FOLDER = "seasons/rules-documents"

_SIGNATURES = (
    (b"%PDF-", "application/pdf", "pdf"),
    (
        b"PK\x03\x04",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "docx",
    ),
)


def sniff_season_rules_document(data: bytes) -> tuple[str, str] | None:
    for magic, content_type, ext in _SIGNATURES:
        if data.startswith(magic):
            return content_type, ext
    return None
