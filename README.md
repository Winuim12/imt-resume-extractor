# IMT Resume Extraction Test

This project is a practical starter for the IMT AI Intern engineering test from `AI_Intern_Test_2404.pdf`.

## Documentation

- Implementation report: [docs/implementation-report.md](docs/implementation-report.md)

## Demo Video

- Demo video: `Add your video link here`
- Suggested content:
  - dataset preprocessing
  - OCR fallback example
  - extracted JSON output
  - question answering across resumes

## What the test asks for

Build a user-facing tool that uses an LLM to extract structured information from resumes.

Core requirements from the PDF:

1. Support resume files from the Kaggle dataset:
   - `HUMAN RESOURCES`
   - `INFORMATION SYSTEMS`
2. Handle both:
   - text-based PDFs
   - scanned PDFs that need OCR
3. Extract entities into structured JSON
4. Provide a lightweight product UI where users can upload/query documents
5. Include an evaluation approach if possible

## Recommended scope for a strong submission

To keep the project realistic and finishable in 6-8 hours, this repo is scoped as:

1. Offline preprocessing pipeline for the full dataset
2. `Streamlit` app for querying the preprocessed corpus
3. `PyPDF` for text PDFs
4. `pytesseract` OCR fallback for scanned PDFs
5. `Ollama` local LLM client for structured extraction and answers
6. Lightweight local RAG over the preprocessed corpus
7. One JSON export per PDF

This is enough to demonstrate:

- end-to-end system design
- OCR-aware ingestion
- LLM extraction
- resume question-answering
- product thinking
- evaluation thinking

## Suggested architecture

```text
Raw resume PDFs
  -> detect text layer
  -> OCR fallback if needed
  -> clean text
  -> extract one structured JSON file per PDF
  -> save plain text and JSON outputs
  -> Streamlit UI loads the preprocessed corpus
  -> build a local TF-IDF retrieval index in memory
  -> answer questions across the whole processed document set
```

## Project structure

```text
IMT-Test/
  app.py
  requirements.txt
  .env
  src/
    config.py
    dataset_loader.py
    extractor.py
    pdf_loader.py
    prompts.py
    rag.py
    schemas.py
    evaluation.py
```

## Setup

1. Create a virtual environment
2. Install dependencies
3. Create a `.env` file
4. Set your Ollama settings in `.env`
5. Run the app

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Environment variables

The app is configured for local Ollama only.

It uses Ollama's OpenAI-compatible local endpoint:

- `OLLAMA_BASE_URL=http://localhost:11434/v1`
- `OLLAMA_MODEL=gpt-oss:20b`
- `OLLAMA_API_KEY=ollama`

Before running the app, make sure Ollama is installed, running, and the model is pulled:

Example `.env`:

```env
OLLAMA_BASE_URL=http://localhost:11434/v1
OLLAMA_API_KEY=ollama
OLLAMA_MODEL=gpt-oss:20b
TESSERACT_CMD=
```

Before using the local path, make sure the Ollama model exists on your machine:

```bash
ollama pull gpt-oss:20b
```

## OCR note

For scanned PDFs, install Tesseract locally and make sure it is available on your PATH.

Windows example:

- Install Tesseract OCR
- Optionally set `TESSERACT_CMD` in `.env`

If OCR is not installed, text PDFs still work and scanned PDFs will return a clear warning.

## Dataset note

Only use files from the Kaggle folders required by the test:

- `HUMAN RESOURCES`
- `INFORMATION SYSTEMS`

Suggested local layout:

```text
data/
  HR/
  INFORMATION-TECHNOLOGY/
```

Manual dataset setup:

1. Download the dataset manually from Kaggle
2. Extract it anywhere on your machine
3. Copy only the required department folders into this project:

```text
IMT-Test/
  data/
    HR/
    INFORMATION-TECHNOLOGY/
```

If the original dataset folder names are different, rename them before placing them into `data/`:

- `HUMAN RESOURCES` -> `HR`
- `INFORMATION SYSTEMS` or `INFORMATION TECHNOLOGY` -> `INFORMATION-TECHNOLOGY`

The Streamlit app supports two input modes:

1. `Use local dataset`: choose one or many PDFs directly from the required Kaggle folders
2. `Upload PDF files`: upload one or many files manually

When a batch is processed:

- each PDF is parsed independently
- one JSON file is written for each PDF under `outputs/profiles/`
- the app builds a shared local RAG index across all successfully processed files
- questions are answered against the whole processed collection, not just one resume

## Preprocess First Workflow

For larger datasets, the recommended workflow is to preprocess the full corpus before opening the UI.

This command:

- reads the PDF dataset
- extracts plain text
- creates one JSON profile per PDF
- saves a manifest for the processed corpus

```bash
python scripts/preprocess_dataset.py
```

Useful options:

- `--department HR`
- `--department INFORMATION-TECHNOLOGY`
- `--limit 20`
- `--skip-existing`
- `--failed-only`

Generated artifacts:

- `outputs/profiles/` for extracted JSON files
- `outputs/texts/` for extracted plain text
- `outputs/manifest.json` for corpus metadata

After preprocessing, run:

```bash
streamlit run app.py
```

The app then loads the preprocessed corpus and answers questions across all indexed resumes.

## Batch Evaluation

You can run a quick batch evaluation from the command line and export the results to CSV.

Example with local Ollama:

```bash
python scripts/run_evaluation.py --model gpt-oss:20b --limit 10
```

Useful options:

- `--department HR`
- `--department INFORMATION-TECHNOLOGY`
- `--limit 20`
- `--output results/evaluation_results.csv`

The exported CSV includes:

- file name
- department
- ingestion method
- page count
- ingestion time
- required field completion rate
- provider and model used
- success or error status
- total runtime

## Evaluation Methodology

This project includes a lightweight but practical evaluation flow designed for an intern take-home scope.

The current evaluation focuses on three questions:

1. Can the system read the resume successfully?
2. Can the extraction pipeline return a usable structured JSON object?
3. How stable is the pipeline in terms of completeness and runtime across multiple files?

### What is measured

Each evaluation row in the CSV represents one resume file and contains the following signals:

- `ingestion_method`
  - `text-layer` if the PDF text could be extracted directly
  - `ocr` if the pipeline had to fall back to OCR
- `page_count`
  - number of pages in the source PDF
- `ingestion_seconds`
  - time spent extracting text from the PDF
- `required_field_completion_rate`
  - completeness score for core extracted fields
- `status`
  - whether the full extraction run succeeded or failed
- `total_runtime_seconds`
  - total time for the end-to-end extraction run

### Completeness metric

The current structured extraction completeness score is based on five required fields:

- `candidate_name`
- `email`
- `skills`
- `education`
- `experience`

The score is calculated as:

```text
filled_required_fields / 5
```

Example:

- `1.0` means all required fields were present
- `0.6` means 3 out of 5 required fields were present

This is not a semantic correctness score. It is a pipeline completeness score that helps identify whether the extraction output is sufficiently usable.

### How to interpret the CSV

In practice, the CSV helps answer:

- Which files succeed consistently?
- Which resumes require OCR?
- How much slower are OCR cases than text-layer PDFs?
- Which model produces more complete structured outputs?
- Which files fail and need prompt or OCR improvements?

### Recommended evaluation workflow

For a short but credible evaluation section in the submission:

1. Run evaluation on a small balanced subset:
   - 10 HR resumes
   - 10 IT resumes
2. Compute:
   - success rate
   - average completion rate
   - average runtime
   - OCR vs text-layer counts
3. Manually review a few extracted JSON outputs
4. Note common failure cases

### Example commands

Evaluate 10 files total:

```bash
python scripts/run_evaluation.py --model gpt-oss:20b --limit 10 --output results/eval_10.csv
```

Evaluate 10 HR files:

```bash
python scripts/run_evaluation.py --department HR --model gpt-oss:20b --limit 10 --output results/eval_hr_10.csv
```

Evaluate 10 IT files:

```bash
python scripts/run_evaluation.py --department INFORMATION-TECHNOLOGY --model gpt-oss:20b --limit 10 --output results/eval_it_10.csv
```

### Limitations of the current evaluation

The current evaluation is intentionally lightweight. It does not yet measure:

- exact correctness of extracted fields against labeled ground truth
- semantic accuracy of every answer in the QA interface
- retrieval precision using annotated relevance judgments

For a stronger follow-up version, the next step would be to create a small manually labeled benchmark and compare:

- extracted name vs true name
- extracted email vs true email
- skill overlap between prediction and manual annotation
- answer correctness on a fixed QA set

## What to demo in the final submission

Good demo flow:

1. Upload one HR resume PDF
2. Show extracted JSON
3. Ask questions like:
   - "What recruiting tools has this candidate used?"
   - "How many years of experience do they appear to have?"
4. Upload one IS resume PDF
5. Repeat extraction + QA
6. Show one scanned PDF case and explain OCR fallback

## Evaluation ideas

The PDF says evaluation is optional but valuable. A good practical section in the README:

1. Extraction validity:
   - JSON parse success rate
   - required field completion rate
2. Retrieval quality:
   - whether the answer cites relevant chunks
   - manual spot-check on top-k retrieved chunks
3. Answer quality:
   - human review for correctness
   - exact-match or rubric-based scoring on a small labeled subset
4. Latency:
   - parse time
   - extraction time
   - answer time

## Suggested delivery strategy

If time is tight, build in this order:

1. PDF text extraction
2. LLM structured JSON extraction
3. Streamlit UI
4. QA over document
5. OCR fallback
6. Evaluation section in README

## Submission checklist

- source code in GitHub
- README with architecture and setup
- screenshots or short GIF of the app
- explanation of OCR strategy
- explanation of extraction schema
- explanation of evaluation approach

## Honest positioning for interview review

If some parts are partial, say so directly in the README. For example:

- OCR fallback implemented, but quality depends on local Tesseract setup
- retrieval uses TF-IDF baseline for clarity and speed
- evaluation uses a small manually reviewed subset due time constraints

That kind of honesty usually reads well when the implementation is otherwise clean and thoughtful.
