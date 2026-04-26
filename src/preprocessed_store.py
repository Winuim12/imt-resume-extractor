import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path

from src.dataset_loader import project_root


def outputs_dir() -> Path:
    path = project_root() / "outputs"
    path.mkdir(parents=True, exist_ok=True)
    return path


def profiles_dir() -> Path:
    path = outputs_dir() / "profiles"
    path.mkdir(parents=True, exist_ok=True)
    return path


def texts_dir() -> Path:
    path = outputs_dir() / "texts"
    path.mkdir(parents=True, exist_ok=True)
    return path


def manifest_path() -> Path:
    return outputs_dir() / "manifest.json"


def preprocess_errors_path() -> Path:
    return outputs_dir() / "preprocess_errors.json"


def _safe_slug(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("_")
    return slug or "item"


def profile_output_path(file_name: str, department: str) -> Path:
    return profiles_dir() / f"{_safe_slug(department)}__{_safe_slug(Path(file_name).stem)}.json"


def text_output_path(file_name: str, department: str) -> Path:
    return texts_dir() / f"{_safe_slug(department)}__{_safe_slug(Path(file_name).stem)}.txt"


@dataclass
class ManifestRecord:
    file_name: str
    department: str
    source_path: str
    profile_path: str
    text_path: str
    ingestion_method: str
    page_count: int
    ingestion_seconds: float
    required_field_completion_rate: float


def save_manifest(records: list[ManifestRecord], merge: bool = True) -> Path:
    path = manifest_path()
    payload: list[dict] = []

    if merge and path.exists():
        existing = json.loads(path.read_text(encoding="utf-8"))
        index = {
            (item["department"], item["file_name"]): item
            for item in existing
        }
        for record in records:
            index[(record.department, record.file_name)] = asdict(record)
        payload = list(index.values())
    else:
        payload = [asdict(record) for record in records]

    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def load_manifest() -> list[ManifestRecord]:
    path = manifest_path()
    if not path.exists():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    return [ManifestRecord(**item) for item in payload]


def load_preprocess_errors() -> list[dict]:
    path = preprocess_errors_path()
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def save_preprocess_errors(errors: list[dict]) -> Path:
    path = preprocess_errors_path()
    path.write_text(json.dumps(errors, indent=2), encoding="utf-8")
    return path


def upsert_preprocess_error(error_record: dict) -> Path:
    errors = load_preprocess_errors()
    index = {
        (item["department"], item["file_name"]): item
        for item in errors
    }
    index[(error_record["department"], error_record["file_name"])] = error_record
    return save_preprocess_errors(list(index.values()))


def remove_preprocess_error(file_name: str, department: str) -> None:
    errors = load_preprocess_errors()
    filtered = [
        item for item in errors
        if not (item["department"] == department and item["file_name"] == file_name)
    ]
    path = preprocess_errors_path()
    if filtered:
        save_preprocess_errors(filtered)
    elif path.exists():
        path.unlink()
