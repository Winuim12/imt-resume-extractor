import tempfile
from dataclasses import dataclass
from pathlib import Path


@dataclass
class InputResume:
    file_name: str
    department: str
    local_path: Path


def save_uploaded_file(uploaded_file) -> Path:
    suffix = Path(uploaded_file.name).suffix or ".pdf"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded_file.getvalue())
        return Path(tmp.name)
