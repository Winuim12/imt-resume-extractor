import argparse
import sys
from pathlib import Path
from types import SimpleNamespace

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.dataset_loader import ALLOWED_DEPARTMENTS, list_dataset_files
from src.preprocessed_store import (
    load_preprocess_errors,
    manifest_path,
    preprocess_errors_path,
    profile_output_path,
    remove_preprocess_error,
    text_output_path,
    upsert_preprocess_error,
)
from src.pipeline import process_resume_file, save_processed_manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Preprocess the dataset into extracted texts, per-file JSON, and a reusable manifest."
    )
    parser.add_argument(
        "--department",
        choices=["ALL", *ALLOWED_DEPARTMENTS],
        default="ALL",
        help="Limit preprocessing to one department.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Maximum number of files to preprocess. Use 0 for all files.",
    )
    parser.add_argument(
        "--failed-only",
        action="store_true",
        help="Retry only files listed in outputs/preprocess_errors.json.",
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Skip files that already have both extracted text and JSON outputs.",
    )
    return parser.parse_args()


def _load_failed_files() -> list[dict]:
    errors = load_preprocess_errors()
    if not errors:
        raise SystemExit(f"No preprocess error file found at: {preprocess_errors_path()}")
    return errors


def _build_retry_items(failed_items: list[dict]) -> list:
    items = []
    for item in failed_items:
        items.append(
            SimpleNamespace(
                department=item["department"],
                path=Path(item["source_path"]),
            )
        )
    return items


def _filter_existing_outputs(files: list) -> list:
    filtered = []
    for item in files:
        profile_path = profile_output_path(item.path.name, item.department)
        text_path = text_output_path(item.path.name, item.department)
        if profile_path.exists() and text_path.exists():
            continue
        filtered.append(item)
    return filtered


def main() -> None:
    args = parse_args()
    if args.failed_only:
        files = _build_retry_items(_load_failed_files())
    else:
        files = list_dataset_files()

    if args.department != "ALL":
        files = [item for item in files if item.department == args.department]
    if args.skip_existing:
        files = _filter_existing_outputs(files)
    if args.limit > 0:
        files = files[: args.limit]

    if not files:
        raise SystemExit("No matching PDF files found.")

    processed = []
    for idx, item in enumerate(files, start=1):
        print(f"[{idx}/{len(files)}] Preprocessing {item.department} | {item.path.name}")
        try:
            processed_item = process_resume_file(item.path, item.path.name, item.department)
            processed.append(processed_item)
            save_processed_manifest([processed_item])
            remove_preprocess_error(file_name=item.path.name, department=item.department)
        except Exception as exc:
            upsert_preprocess_error(
                {
                    "file_name": item.path.name,
                    "department": item.department,
                    "source_path": str(item.path),
                    "error": str(exc),
                }
            )
            print(f"  -> skipped due to error: {exc}")

    if not processed:
        raise SystemExit("No files were processed successfully.")

    manifest = manifest_path()
    print(f"Saved manifest: {manifest}")

    current_errors = load_preprocess_errors()
    if current_errors:
        print(f"Saved preprocessing errors: {preprocess_errors_path()}")
    elif args.failed_only:
        print("Cleared preprocess error file because all retries succeeded.")

    print("Preprocessing completed. The current app queries the preprocessed corpus with a local TF-IDF RAG index.")


if __name__ == "__main__":
    main()
