# IMT Resume Extraction Test

This project is a practical starter for the IMT AI Intern engineering test from `AI_Intern_Test_2404.pdf`.

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

1. `Streamlit` app for upload + extraction + QA
2. `PyPDF` for text PDFs
3. `pytesseract` OCR fallback for scanned PDFs
4. `Ollama` local LLM client for structured extraction and answers
5. `TF-IDF retrieval` for a simple, explainable RAG baseline
6. JSON export for extracted candidate profile

This is enough to demonstrate:

- end-to-end system design
- OCR-aware ingestion
- LLM extraction
- resume question-answering
- product thinking
- evaluation thinking

## Suggested architecture

```text
Upload PDF
  -> detect text layer
  -> OCR fallback if needed
  -> clean text
  -> chunk text for retrieval
  -> extract structured JSON with LLM
  -> allow QA over retrieved chunks
  -> export JSON + latency/debug info
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

1. `Use local dataset`: choose PDFs directly from the required Kaggle folders
2. `Upload PDF`: upload a file manually for quick testing

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
