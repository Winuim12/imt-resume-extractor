from dataclasses import dataclass
import re

from openai import OpenAI
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from src.config import settings
from src.prompts import build_qa_prompt


def _chunk_text(text: str, chunk_size: int = 900, overlap: int = 150) -> list[str]:
    if not text.strip():
        return []

    chunks = []
    start = 0
    while start < len(text):
        end = min(len(text), start + chunk_size)
        chunks.append(text[start:end])
        if end == len(text):
            break
        start = max(0, end - overlap)
    return chunks


@dataclass
class ResumeChunk:
    file_name: str
    department: str
    text: str
    kind: str = "content"


@dataclass
class SimpleResumeIndex:
    chunks: list[ResumeChunk]
    vectorizer: TfidfVectorizer
    matrix: object

    @classmethod
    def from_text(cls, text: str) -> "SimpleResumeIndex":
        chunks = [
            ResumeChunk(
                file_name="uploaded_resume.pdf",
                department="UNKNOWN",
                text=chunk,
                kind="content",
            )
            for chunk in _chunk_text(text)
        ]
        vectorizer = TfidfVectorizer(stop_words="english")
        matrix = vectorizer.fit_transform([chunk.text for chunk in chunks]) if chunks else None
        return cls(chunks=chunks, vectorizer=vectorizer, matrix=matrix)

    @classmethod
    def from_documents(cls, documents: list[dict]) -> "SimpleResumeIndex":
        chunks: list[ResumeChunk] = []
        for document in documents:
            summary_text = document.get("summary_text", "").strip()
            if summary_text:
                chunks.append(
                    ResumeChunk(
                        file_name=document["file_name"],
                        department=document["department"],
                        text=summary_text,
                        kind="summary",
                    )
                )
            for chunk in _chunk_text(document["text"]):
                chunks.append(
                    ResumeChunk(
                        file_name=document["file_name"],
                        department=document["department"],
                        text=chunk,
                        kind="content",
                    )
                )
        vectorizer = TfidfVectorizer(stop_words="english")
        matrix = vectorizer.fit_transform([chunk.text for chunk in chunks]) if chunks else None
        return cls(chunks=chunks, vectorizer=vectorizer, matrix=matrix)

    def search(self, query: str, top_k: int = 4) -> list[ResumeChunk]:
        if not self.chunks or self.matrix is None:
            return []
        query_vector = self.vectorizer.transform([query])
        scores = cosine_similarity(query_vector, self.matrix)[0]
        query_terms = {
            term.lower()
            for term in re.findall(r"[A-Za-z0-9+#.\-]+", query)
            if len(term) > 1
        }
        boosted = []
        for chunk, score in zip(self.chunks, scores):
            adjusted = float(score)
            lower_text = chunk.text.lower()
            overlap_count = sum(1 for term in query_terms if term in lower_text)
            adjusted += overlap_count * 0.08
            if chunk.kind == "summary":
                adjusted += 0.25
                adjusted += overlap_count * 0.12
            boosted.append((chunk, adjusted))
        ranked = sorted(
            boosted,
            key=lambda item: item[1],
            reverse=True,
        )
        return [chunk for chunk, _ in ranked[:top_k]]


def answer_question(question: str, index: SimpleResumeIndex, top_k: int = 4) -> dict:
    chunks = index.search(question, top_k=top_k)
    context = "\n\n".join(
        [
            f"Source file: {chunk.file_name}\nDepartment: {chunk.department}\nContent:\n{chunk.text}"
            for chunk in chunks
        ]
    )

    client = OpenAI(
        api_key=settings.resolved_api_key,
        base_url=settings.ollama_base_url,
    )
    response = client.chat.completions.create(
        model=settings.ollama_model,
        temperature=0,
        messages=[
            {
                "role": "user",
                "content": build_qa_prompt(question=question, context=context),
            }
        ],
    )

    return {
        "answer": response.choices[0].message.content,
        "chunks": [
            {
                "file_name": chunk.file_name,
                "department": chunk.department,
                "text": chunk.text,
            }
            for chunk in chunks
        ],
    }
