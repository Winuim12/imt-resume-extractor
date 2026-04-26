from dataclasses import dataclass

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
class SimpleResumeIndex:
    chunks: list[str]
    vectorizer: TfidfVectorizer
    matrix: object

    @classmethod
    def from_text(cls, text: str) -> "SimpleResumeIndex":
        chunks = _chunk_text(text)
        vectorizer = TfidfVectorizer(stop_words="english")
        matrix = vectorizer.fit_transform(chunks) if chunks else None
        return cls(chunks=chunks, vectorizer=vectorizer, matrix=matrix)

    def search(self, query: str, top_k: int = 4) -> list[str]:
        if not self.chunks or self.matrix is None:
            return []
        query_vector = self.vectorizer.transform([query])
        scores = cosine_similarity(query_vector, self.matrix)[0]
        ranked = sorted(
            zip(self.chunks, scores),
            key=lambda item: item[1],
            reverse=True,
        )
        return [chunk for chunk, _ in ranked[:top_k]]


def answer_question(question: str, index: SimpleResumeIndex, top_k: int = 4) -> dict:
    chunks = index.search(question, top_k=top_k)
    context = "\n\n".join(chunks)

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
        "chunks": chunks,
    }
