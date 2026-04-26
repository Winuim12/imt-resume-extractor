import json
import re

from openai import OpenAI

from src.config import settings
from src.prompts import EXTRACTION_SYSTEM_PROMPT, build_extraction_prompt
from src.schemas import ResumeProfile


def _client() -> OpenAI:
    return OpenAI(
        api_key=settings.resolved_api_key,
        base_url=settings.ollama_base_url,
    )


def _extract_json_object(content: str) -> dict:
    content = content.strip()

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass

    fenced_match = re.search(r"```(?:json)?\s*(\{.*\})\s*```", content, re.DOTALL)
    if fenced_match:
        return json.loads(fenced_match.group(1))

    start = content.find("{")
    end = content.rfind("}")
    if start != -1 and end != -1 and end > start:
        return json.loads(content[start : end + 1])

    raise ValueError("The model response did not contain valid JSON.")


def extract_resume_profile(raw_text: str, department: str) -> dict:
    client = _client()
    response = client.chat.completions.create(
        model=settings.ollama_model,
        temperature=0,
        messages=[
            {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": build_extraction_prompt(raw_text=raw_text, department=department),
            },
        ],
    )
    payload = response.choices[0].message.content
    parsed = _extract_json_object(payload)
    return ResumeProfile.model_validate(parsed).model_dump()
