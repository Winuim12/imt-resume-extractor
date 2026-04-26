# Implementation Report

## Objective

This tool was built to process resumes from the IMT test dataset, extract structured candidate information with an LLM, and provide a simple interface for querying the processed corpus.

## Technology Stack

- `Python` for the end-to-end pipeline
- `Streamlit` for the lightweight UI
- `pypdf` for text extraction from text-based PDFs
- `PyMuPDF` + `pytesseract` + `Pillow` for OCR fallback on scanned PDFs
- `OpenAI Python SDK` pointed to the local Ollama OpenAI-compatible endpoint
- `Pydantic` for structured schema validation
- `scikit-learn` TF-IDF + cosine similarity for local retrieval
- `json-repair` as a fallback when the model returns malformed JSON

## Implementation Approach

The implementation is split into three stages:

1. Ingestion
   - The system reads a resume PDF and first tries to extract text directly with `pypdf`.
   - If the extracted text is too short, it assumes the file is scanned and falls back to OCR using `PyMuPDF` page rendering and `pytesseract`.

2. Structured extraction
   - The extracted resume text is sent to the local LLM through Ollama's OpenAI-compatible API.
   - The model is prompted to return a structured JSON profile.
   - The response is parsed and validated against the `ResumeProfile` schema.
   - If the JSON is malformed, the app first tries local repair logic and then an LLM-based repair pass.

3. Storage and retrieval
   - For each processed resume, the app stores:
     - raw extracted text in `outputs/texts/`
     - structured profile JSON in `outputs/profiles/`
     - metadata in `outputs/manifest.json`
   - When the Streamlit app loads, it reads the manifest and builds a local TF-IDF index over enriched resume content.
   - User questions are answered by retrieving the most relevant chunks and sending that context back to the local LLM.

## Workflow

```text
Resume PDF
  -> extract text with pypdf
  -> if text is insufficient, run OCR fallback
  -> send cleaned resume text to Ollama
  -> validate and repair JSON if needed
  -> save text, profile, and manifest record
  -> build TF-IDF index over processed resumes
  -> answer user questions from retrieved evidence
```

## Product Flow

There are two practical usage flows in this project:

1. Preprocess-first flow
   - Run `python scripts/preprocess_dataset.py`
   - Build the local corpus before opening the UI
   - Use the app to inspect processed resumes and ask cross-document questions

2. Incremental upload flow
   - Open the Streamlit app
   - Upload new PDFs from an allowed department
   - Merge new processed files into the existing corpus
   - Rebuild the in-memory retrieval index on demand

## Why This Design

- The OCR fallback makes the tool usable for both text-layer and scanned resumes.
- Saving intermediate artifacts improves debugging and makes evaluation easier.
- A local TF-IDF retriever is simple, fast, and easy to explain in a take-home assignment.
- Using a schema-validated JSON output keeps the extraction result structured and consistent.

## Current Limitations

- OCR quality depends on the local Tesseract installation and scan quality.
- Retrieval is lexical TF-IDF, so it is weaker than embedding-based search for semantic matching.
- The evaluation currently measures pipeline completeness and runtime, not full field-level correctness against labeled ground truth.

## Key Output Files

- `outputs/profiles/*.json`: extracted structured candidate profiles
- `outputs/texts/*.txt`: extracted resume text
- `outputs/manifest.json`: corpus-level metadata for the UI
- `results/*.csv`: optional evaluation exports
