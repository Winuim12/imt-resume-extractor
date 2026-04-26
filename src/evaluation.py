from src.pdf_loader import ExtractionResult


def make_run_stats(
    file_name: str,
    department: str,
    extraction: ExtractionResult,
    profile: dict,
) -> dict:
    required_fields = [
        "candidate_name",
        "email",
        "skills",
        "education",
        "experience",
    ]
    filled = 0
    for field in required_fields:
        value = profile.get(field)
        if value not in (None, "", []):
            filled += 1

    return {
        "file_name": file_name,
        "department": department,
        "ingestion_method": extraction.method,
        "page_count": extraction.page_count,
        "ingestion_seconds": extraction.elapsed_seconds,
        "required_field_completion_rate": round(filled / len(required_fields), 2),
    }
