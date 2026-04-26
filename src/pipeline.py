import json
import re
from dataclasses import dataclass
from pathlib import Path

from src.evaluation import make_run_stats
from src.extractor import extract_resume_profile
from src.pdf_loader import extract_resume_text
from src.preprocessed_store import (
    ManifestRecord,
    profile_output_path,
    save_manifest,
    text_output_path,
)


@dataclass
class ProcessedResume:
    file_name: str
    department: str
    source_path: Path
    profile_path: Path
    text_path: Path
    text: str
    run_stats: dict


def process_resume_file(local_path: Path, file_name: str, department: str) -> ProcessedResume:
    extraction = extract_resume_text(local_path)
    profile = extract_resume_profile(raw_text=extraction.text, department=department)

    output_path = profile_output_path(file_name=file_name, department=department)
    output_path.write_text(json.dumps(profile, indent=2), encoding="utf-8")
    extracted_text_path = text_output_path(file_name=file_name, department=department)
    extracted_text_path.write_text(extraction.text, encoding="utf-8")

    run_stats = make_run_stats(
        file_name=file_name,
        department=department,
        extraction=extraction,
        profile=profile,
    )
    run_stats["profile_output_path"] = str(output_path)

    return ProcessedResume(
        file_name=file_name,
        department=department,
        source_path=local_path,
        profile_path=output_path,
        text_path=extracted_text_path,
        text=extraction.text,
        run_stats=run_stats,
    )


def save_processed_manifest(processed_resumes: list[ProcessedResume]) -> Path:
    records = [
        ManifestRecord(
            file_name=item.file_name,
            department=item.department,
            source_path=str(item.source_path),
            profile_path=str(item.profile_path),
            text_path=str(item.text_path),
            ingestion_method=item.run_stats["ingestion_method"],
            page_count=item.run_stats["page_count"],
            ingestion_seconds=item.run_stats["ingestion_seconds"],
            required_field_completion_rate=item.run_stats["required_field_completion_rate"],
        )
        for item in processed_resumes
    ]
    return save_manifest(records)
