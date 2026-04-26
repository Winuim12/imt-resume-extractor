import argparse
import csv
import sys
from pathlib import Path
from time import perf_counter

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import settings
from src.dataset_loader import ALLOWED_DEPARTMENTS, list_dataset_files
from src.evaluation import make_run_stats
from src.extractor import extract_resume_profile
from src.pdf_loader import extract_resume_text


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run batch evaluation over resume PDFs and export CSV results."
    )
    parser.add_argument(
        "--department",
        choices=["ALL", *ALLOWED_DEPARTMENTS],
        default="ALL",
        help="Limit evaluation to one department.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Maximum number of files to process per run.",
    )
    parser.add_argument(
        "--output",
        default="evaluation_results.csv",
        help="Output CSV path relative to project root or absolute path.",
    )
    parser.add_argument(
        "--model",
        default="",
        help="Override Ollama model name.",
    )
    return parser.parse_args()


def select_files(args: argparse.Namespace) -> list:
    files = list_dataset_files()
    if args.department != "ALL":
        files = [item for item in files if item.department == args.department]
    return files[: args.limit]


def normalize_output_path(output_arg: str) -> Path:
    output_path = Path(output_arg)
    if not output_path.is_absolute():
        output_path = PROJECT_ROOT / output_path
    output_path.parent.mkdir(parents=True, exist_ok=True)
    return output_path


def main() -> None:
    args = parse_args()
    files = select_files(args)
    output_path = normalize_output_path(args.output)
    ollama_model = args.model or settings.ollama_model

    if not files:
        raise SystemExit("No matching PDF files found in the dataset.")

    rows = []
    print("Provider: ollama")
    print(f"Base URL: {settings.ollama_base_url}")
    print(f"Model: {ollama_model}")
    print(f"Files to process: {len(files)}")
    print("")

    for index, item in enumerate(files, start=1):
        print(f"[{index}/{len(files)}] Processing {item.department} | {item.path.name}")
        started_at = perf_counter()
        try:
            extraction = extract_resume_text(item.path)
            original_model = settings.ollama_model
            settings.ollama_model = ollama_model
            profile = extract_resume_profile(
                raw_text=extraction.text,
                department=item.department,
            )
            settings.ollama_model = original_model
            run_stats = make_run_stats(
                file_name=item.path.name,
                department=item.department,
                extraction=extraction,
                profile=profile,
            )
            run_stats["llm_provider"] = "ollama"
            run_stats["llm_model"] = ollama_model
            run_stats["status"] = "success"
            run_stats["error"] = ""
            run_stats["total_runtime_seconds"] = round(perf_counter() - started_at, 2)
            rows.append(run_stats)
        except Exception as exc:
            rows.append(
                {
                    "file_name": item.path.name,
                    "department": item.department,
                    "ingestion_method": "",
                    "page_count": "",
                    "ingestion_seconds": "",
                    "required_field_completion_rate": "",
                    "llm_provider": "ollama",
                    "llm_model": ollama_model,
                    "status": "error",
                    "error": str(exc),
                    "total_runtime_seconds": round(perf_counter() - started_at, 2),
                }
            )

    fieldnames = [
        "file_name",
        "department",
        "ingestion_method",
        "page_count",
        "ingestion_seconds",
        "required_field_completion_rate",
        "llm_provider",
        "llm_model",
        "status",
        "error",
        "total_runtime_seconds",
    ]

    with output_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    success_count = sum(1 for row in rows if row["status"] == "success")
    print("")
    print(f"Saved results to: {output_path}")
    print(f"Success: {success_count}/{len(rows)}")


if __name__ == "__main__":
    main()
