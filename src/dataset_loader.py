from dataclasses import dataclass
from pathlib import Path


DATASET_DEPARTMENT_DIRS = {
    "HR": ("HR", "HUMAN RESOURCES"),
    "INFORMATION-TECHNOLOGY": (
        "INFORMATION-TECHNOLOGY",
        "INFORMATION TECHNOLOGY",
        "INFORMATION SYSTEMS",
    ),
}

ALLOWED_DEPARTMENTS = tuple(DATASET_DEPARTMENT_DIRS.keys())


@dataclass
class DatasetFile:
    department: str
    path: Path

    @property
    def label(self) -> str:
        return f"{self.department} | {self.path.name}"


def project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def default_data_dir() -> Path:
    return project_root() / "data"


def list_dataset_files(data_dir: Path | None = None) -> list[DatasetFile]:
    base_dir = data_dir or default_data_dir()
    files: list[DatasetFile] = []

    for department in ALLOWED_DEPARTMENTS:
        department_dir = base_dir / department
        if department_dir.exists():
            for path in sorted(department_dir.rglob("*")):
                if path.is_file() and path.suffix.lower() == ".pdf":
                    files.append(DatasetFile(department=department, path=path))

    return files


def dataset_summary(data_dir: Path | None = None) -> dict:
    base_dir = data_dir or default_data_dir()
    summary = {
        "base_dir": str(base_dir),
        "available": base_dir.exists(),
        "departments": {},
        "total_files": 0,
    }

    total_files = 0
    for department in ALLOWED_DEPARTMENTS:
        department_dir = base_dir / department
        count = 0
        if department_dir.exists():
            count = len(
                [
                    path
                    for path in department_dir.rglob("*")
                    if path.is_file() and path.suffix.lower() == ".pdf"
                ]
            )
        summary["departments"][department] = count
        total_files += count

    summary["total_files"] = total_files
    return summary
