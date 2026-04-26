# Demo Video Script

This is a short speaking script for a 2-4 minute demo video of the project.

## Demo goal

Show that the system can:

1. load resumes from the required dataset folders
2. handle resume parsing end-to-end
3. extract structured JSON from unstructured CVs
4. answer questions over the selected resume
5. support evaluation with a simple batch workflow

## Suggested demo length

- Short version: 2 minutes
- Full version: 3-4 minutes

## Before recording

Prepare these items:

1. Run Ollama locally
2. Start the Streamlit app
3. Make sure the dataset folders are available:
   - `data/HR`
   - `data/INFORMATION-TECHNOLOGY`
4. Pick:
   - one HR resume
   - one IT resume
5. Keep one evaluation CSV ready, such as:
   - `results/eval_10.csv`

## Opening script

Hello, this is my submission for the IMT AI Intern engineering test.

In this project, I built a Streamlit-based resume extraction tool that uses a local LLM through Ollama to extract structured information from resumes and support question answering over each document.

The system is designed around the test requirements: handling resumes from the HR and Information Technology categories, supporting text-based PDFs and scanned PDFs through OCR fallback, and providing a lightweight user-facing interface.

## Part 1: Show the app

While showing the app home screen:

This is the main application interface.

On the left, the app shows the local dataset path and the available resume counts for the two required categories.

The app is currently configured to run locally with Ollama, which means it does not depend on a paid cloud API during execution.

## Part 2: Process one HR resume

While selecting an HR file:

First, I select a resume from the HR folder and process it.

The pipeline first reads the PDF. If the file has a text layer, it extracts text directly. If not, it falls back to OCR.

Then the extracted text is passed to the LLM, which returns a structured JSON representation of the candidate profile.

When the JSON appears:

Here we can see the structured extraction output, including core fields such as the candidate name, email, skills, education, and experience.

On the right side, the app also shows run statistics such as ingestion method, page count, processing time, and the required field completion rate.

## Part 3: Ask questions about the resume

While entering a question:

In addition to structured extraction, the app also supports lightweight retrieval-based question answering over the selected resume.

For example, I can ask what skills or tools the candidate has used, or estimate their years of experience based on the content of the resume.

When the answer appears:

The answer is generated from the retrieved chunks of the selected resume, and the app also shows the supporting context used for the response.

## Part 4: Show a second resume from IT

While switching to an IT resume:

Next, I repeat the same workflow on a resume from the Information Technology folder to show that the same pipeline works across both required departments.

This helps demonstrate that the solution is not hard-coded for a single resume type.

## Part 5: Mention OCR support

You do not need to force an OCR example on video unless you already have a good scanned file ready.

Suggested line:

The ingestion pipeline also includes an OCR fallback path for scanned PDFs. If a PDF does not contain enough text in its text layer, the system switches to OCR using Tesseract.

## Part 6: Show evaluation

While opening `eval_10.csv` or terminal output:

I also included a simple batch evaluation script to measure extraction stability across multiple resumes.

The evaluation exports a CSV with metrics such as ingestion method, runtime, success status, and required field completion rate.

This evaluation is intentionally lightweight for the scope of the take-home test, but it gives a practical view of system reliability and extraction completeness.

## Closing script

To summarize, this project demonstrates an end-to-end local resume extraction workflow with:

1. PDF ingestion
2. OCR fallback for scanned files
3. structured JSON extraction with an LLM
4. question answering over each resume
5. a simple batch evaluation pipeline

Thank you for reviewing my submission.

## Very short 60-second version

Hello, this is my submission for the IMT AI Intern test.

This app uses Streamlit and a local Ollama model to extract structured information from resumes in the required HR and IT folders.

Here I select a resume, process it, and the system extracts plain text, converts it into structured JSON, and shows runtime statistics.

I can also ask questions about the selected resume, and the app answers using retrieved resume chunks.

Finally, I included a batch evaluation script that exports CSV results to measure extraction completeness, runtime, and success rate across multiple files.

Thank you for your time.
