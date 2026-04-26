import json
import tempfile
from pathlib import Path

import streamlit as st

from src.config import settings
from src.dataset_loader import ALLOWED_DEPARTMENTS, dataset_summary, list_dataset_files
from src.evaluation import make_run_stats
from src.extractor import extract_resume_profile
from src.pdf_loader import extract_resume_text
from src.rag import SimpleResumeIndex, answer_question


st.set_page_config(page_title="IMT Resume Extractor", layout="wide")


def _save_upload(uploaded_file) -> Path:
    suffix = Path(uploaded_file.name).suffix or ".pdf"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded_file.getvalue())
        return Path(tmp.name)


def _process_resume(
    local_path: Path,
    file_name: str,
    department: str,
) -> None:
    with st.spinner("Reading PDF and extracting candidate data..."):
        extraction = extract_resume_text(local_path)
        profile = extract_resume_profile(
            raw_text=extraction.text,
            department=department,
        )
        index = SimpleResumeIndex.from_text(extraction.text)
        run_stats = make_run_stats(
            file_name=file_name,
            department=department,
            extraction=extraction,
            profile=profile,
        )

    st.session_state.resume_text = extraction.text
    st.session_state.resume_index = index
    st.session_state.resume_profile = profile
    st.session_state.run_stats = run_stats
    st.session_state.source_file_name = file_name


st.title("IMT Resume Extractor")
st.caption("Structured extraction + lightweight RAG over HR and IT resumes")

summary = dataset_summary()
dataset_files = list_dataset_files()

with st.sidebar:
    st.subheader("Settings")
    top_k = st.slider("Retrieved chunks", min_value=1, max_value=8, value=4)
    st.caption("LLM provider: Ollama Local")
    st.caption(f"Active model: {settings.ollama_model}")
    st.caption(f"Endpoint: {settings.ollama_base_url}")
    st.subheader("Dataset")
    st.caption(summary["base_dir"])
    st.json(summary["departments"])

source_mode = st.radio(
    "Choose resume source",
    ["Use local dataset", "Upload PDF"],
    horizontal=True,
)

if "resume_text" not in st.session_state:
    st.session_state.resume_text = ""
if "resume_index" not in st.session_state:
    st.session_state.resume_index = None
if "resume_profile" not in st.session_state:
    st.session_state.resume_profile = None
if "run_stats" not in st.session_state:
    st.session_state.run_stats = None
if "source_file_name" not in st.session_state:
    st.session_state.source_file_name = ""

selected_department = None
selected_dataset_item = None

if source_mode == "Use local dataset":
    if not dataset_files:
        st.warning(
            "No dataset PDFs found yet. Put files under data/HR and data/INFORMATION-TECHNOLOGY."
        )
    else:
        selected_department = st.selectbox(
            "Department",
            ALLOWED_DEPARTMENTS,
        )
        filtered_items = [
            item for item in dataset_files if item.department == selected_department
        ]
        selected_label = st.selectbox(
            "Resume file",
            [item.label for item in filtered_items],
        )
        selected_dataset_item = next(
            item for item in filtered_items if item.label == selected_label
        )

        if st.button("Process Resume", type="primary"):
            try:
                _process_resume(
                    local_path=selected_dataset_item.path,
                    file_name=selected_dataset_item.path.name,
                    department=selected_dataset_item.department,
                )
            except Exception as exc:
                st.error(f"Could not process resume: {exc}")
else:
    selected_department = st.selectbox(
        "Department",
        ALLOWED_DEPARTMENTS,
    )
    uploaded_file = st.file_uploader("Upload a resume PDF", type=["pdf"])
    if uploaded_file and st.button("Process Resume", type="primary"):
        local_path = _save_upload(uploaded_file)
        try:
            _process_resume(
                local_path=local_path,
                file_name=uploaded_file.name,
                department=selected_department,
            )
        except Exception as exc:
            st.error(f"Could not process resume: {exc}")

col_left, col_right = st.columns([1.2, 1.0])

with col_left:
    st.subheader("Structured JSON")
    if st.session_state.resume_profile:
        st.json(st.session_state.resume_profile)
        st.download_button(
            "Download JSON",
            data=json.dumps(st.session_state.resume_profile, indent=2),
            file_name="resume_profile.json",
            mime="application/json",
        )
    else:
        st.info("Upload a PDF and process it to see the extracted candidate profile.")

with col_right:
    st.subheader("Run Stats")
    if st.session_state.run_stats:
        if st.session_state.source_file_name:
            st.caption(f"Current file: {st.session_state.source_file_name}")
        st.json(st.session_state.run_stats)
    else:
        st.info("Processing metadata will appear here.")

st.subheader("Ask Questions About This Resume")
question = st.text_input(
    "Example: What tools has this candidate used, and what evidence supports that?"
)

if st.button("Answer Question") and question:
    if not st.session_state.resume_index:
        st.warning("Please process a resume first.")
    else:
        try:
            with st.spinner("Searching relevant chunks and generating an answer..."):
                qa_result = answer_question(
                    question=question,
                    index=st.session_state.resume_index,
                    top_k=top_k,
                )
            st.markdown(qa_result["answer"])
            with st.expander("Retrieved Context"):
                for idx, chunk in enumerate(qa_result["chunks"], start=1):
                    st.markdown(f"**Chunk {idx}**")
                    st.write(chunk)
        except Exception as exc:
            st.error(f"Could not answer the question: {exc}")

with st.expander("Extracted Plain Text"):
    if st.session_state.resume_text:
        st.text(st.session_state.resume_text[:12000])
    else:
        st.write("No text extracted yet.")
