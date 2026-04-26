from pathlib import Path
import json

import streamlit as st

from src.config import settings
from src.ingestion import save_uploaded_file
from src.pipeline import process_resume_file, save_processed_manifest
from src.preprocessed_store import load_manifest, manifest_path, outputs_dir
from src.rag import SimpleResumeIndex, answer_question
from src.dataset_loader import ALLOWED_DEPARTMENTS


st.set_page_config(page_title="IMT Resume RAG", layout="wide")


def _load_fallback_index(records: list) -> SimpleResumeIndex:
    documents = []
    for record in records:
        text = Path(record.text_path).read_text(encoding="utf-8")
        profile = json.loads(Path(record.profile_path).read_text(encoding="utf-8"))
        skills = ", ".join(profile.get("skills", []))
        tools = ", ".join(profile.get("tools", []))
        certifications = ", ".join(profile.get("certifications", []))
        education = " | ".join(
            [
                " - ".join(
                    [
                        item.get("degree") or "",
                        item.get("institution") or "",
                        item.get("graduation_year") or "",
                    ]
                ).strip(" -")
                for item in profile.get("education", [])
            ]
        )
        experience = " | ".join(
            [
                " - ".join(
                    [
                        item.get("title") or "",
                        item.get("company") or "",
                        item.get("duration") or "",
                        ", ".join(item.get("responsibilities", [])),
                    ]
                ).strip(" -")
                for item in profile.get("experience", [])
            ]
        )
        projects = " | ".join(
            [
                " - ".join(
                    [
                        item.get("name") or "",
                        item.get("description") or "",
                        ", ".join(item.get("technologies", [])),
                    ]
                ).strip(" -")
                for item in profile.get("projects", [])
            ]
        )
        enriched_text = f"""
Candidate Name: {profile.get('candidate_name') or ''}
Department: {profile.get('department') or record.department}
Summary: {profile.get('summary') or ''}
Skills: {skills}
Tools: {tools}
Certifications: {certifications}
Education: {education}
Experience: {experience}
Projects: {projects}

Resume Content:
{text}
""".strip()
        summary_text = f"""
Candidate Name: {profile.get('candidate_name') or ''}
Department: {profile.get('department') or record.department}
Skills: {skills}
Tools: {tools}
Projects: {projects}
Summary: {profile.get('summary') or ''}
""".strip()
        documents.append(
            {
                "file_name": record.file_name,
                "department": record.department,
                "text": enriched_text,
                "summary_text": summary_text,
            }
        )
    return SimpleResumeIndex.from_documents(documents)


def _add_uploaded_documents(uploaded_files, department: str) -> dict:
    processed = []
    errors = []

    for uploaded_file in uploaded_files:
        local_path = save_uploaded_file(uploaded_file)
        try:
            processed_item = process_resume_file(
                local_path=local_path,
                file_name=uploaded_file.name,
                department=department,
            )
            processed.append(processed_item)
            save_processed_manifest([processed_item])
        except Exception as exc:
            errors.append({"file_name": uploaded_file.name, "error": str(exc)})

    return {"processed": processed, "errors": errors}


st.title("IMT Resume RAG")
st.caption("Query a preprocessed multi-document resume corpus")

records = load_manifest()

with st.sidebar:
    st.subheader("Runtime")
    st.caption("LLM provider: Ollama Local")
    st.caption(f"Model: {settings.ollama_model}")
    st.caption(f"Endpoint: {settings.ollama_host}")
    st.subheader("Corpus")
    st.caption(f"Manifest: {manifest_path()}")
    st.caption(f"Outputs: {outputs_dir()}")
    st.caption("Retrieval mode: TF-IDF local RAG over preprocessed corpus")
    top_k = st.slider("Retrieved chunks", min_value=1, max_value=12, value=6)

if "fallback_index" not in st.session_state:
    st.session_state.fallback_index = None

with st.expander("Add New Documents To The Corpus"):
    upload_department = st.selectbox("Upload department", ALLOWED_DEPARTMENTS)
    new_uploaded_files = st.file_uploader(
        "Upload new PDF files to merge into the corpus",
        type=["pdf"],
        accept_multiple_files=True,
        key="corpus_uploader",
    )
    if st.button("Preprocess And Merge Documents", disabled=not new_uploaded_files):
        try:
            with st.spinner("Processing new documents and updating the corpus..."):
                merge_result = _add_uploaded_documents(new_uploaded_files, upload_department)
            st.session_state.fallback_index = None
            if merge_result["processed"]:
                st.success(
                    f"Merged {len(merge_result['processed'])} new document(s) into the corpus."
                )
            if merge_result["errors"]:
                st.warning(f"{len(merge_result['errors'])} file(s) could not be processed.")
                st.json(merge_result["errors"])
            st.rerun()
        except Exception as exc:
            st.error(f"Could not merge new documents into the corpus: {exc}")

if not records:
    st.warning(
        "No preprocessed corpus found yet. Run `python scripts\\preprocess_dataset.py` first."
    )
else:
    col_left, col_right = st.columns([1.15, 0.85])

    with col_left:
        st.subheader("Preprocessed Documents")
        table = [
            {
                "file_name": record.file_name,
                "department": record.department,
                "ingestion_method": record.ingestion_method,
                "pages": record.page_count,
                "ingestion_seconds": record.ingestion_seconds,
                "completion_rate": record.required_field_completion_rate,
                "profile_json": record.profile_path,
            }
            for record in records
        ]
        st.dataframe(table, width="stretch")

    with col_right:
        st.subheader("Corpus Summary")
        total_files = len(records)
        ocr_files = sum(1 for record in records if record.ingestion_method == "ocr")
        avg_completion = round(
            sum(record.required_field_completion_rate for record in records) / total_files,
            2,
        )
        st.json(
            {
                "processed_files": total_files,
                "ocr_files": ocr_files,
                "text_layer_files": total_files - ocr_files,
                "average_completion_rate": avg_completion,
                "retrieval_mode": "tfidf_rag",
            }
        )

    st.subheader("Ask Questions Across The Preprocessed Resume Set")
    question = st.text_input(
        "Example: Which candidates mention Python experience, and what evidence supports that?"
    )

    if st.button("Answer Question") and question:
        try:
            if st.session_state.fallback_index is None:
                st.session_state.fallback_index = _load_fallback_index(records)
            with st.spinner("Querying the preprocessed local index..."):
                qa_result = answer_question(
                    question=question,
                    index=st.session_state.fallback_index,
                    top_k=top_k,
                )
            st.markdown(qa_result["answer"])
            with st.expander("Retrieved Context"):
                for idx, chunk in enumerate(qa_result["chunks"], start=1):
                    st.markdown(f"**Chunk {idx} | {chunk['file_name']} | {chunk['department']}**")
                    st.write(chunk["text"])
        except Exception as exc:
            st.error(f"Could not answer the question: {exc}")
