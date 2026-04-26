import json
import re
from pathlib import Path

from openai import OpenAI
from json_repair import repair_json

from src.config import settings
from src.preprocessed_store import outputs_dir
from src.prompts import (
    EXTRACTION_SYSTEM_PROMPT,
    JSON_REPAIR_SYSTEM_PROMPT,
    build_extraction_prompt,
    build_json_repair_prompt,
)
from src.schemas import ResumeProfile


def _client() -> OpenAI:
    return OpenAI(
        api_key=settings.resolved_api_key,
        base_url=settings.ollama_base_url,
    )


def _extract_json_object(content: str) -> dict:
    content = content.strip()
    content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL | re.IGNORECASE).strip()

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
        candidate = content[start : end + 1]
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass

        try:
            repaired = repair_json(candidate, return_objects=True)
            if isinstance(repaired, dict):
                return repaired
        except Exception:
            pass

    try:
        repaired = repair_json(content, return_objects=True)
        if isinstance(repaired, dict):
            return repaired
    except Exception:
        pass

    raise ValueError("The model response did not contain valid JSON.")


def _save_debug_payload(payload: str, department: str) -> Path:
    debug_dir = outputs_dir() / "debug"
    debug_dir.mkdir(parents=True, exist_ok=True)
    debug_path = debug_dir / f"bad_response_{department}.txt"
    debug_path.write_text(payload, encoding="utf-8")
    return debug_path


def _repair_json_with_llm(client: OpenAI, payload: str) -> dict:
    response = client.chat.completions.create(
        model=settings.ollama_model,
        temperature=0,
        messages=[
            {"role": "system", "content": JSON_REPAIR_SYSTEM_PROMPT},
            {"role": "user", "content": build_json_repair_prompt(payload)},
        ],
    )
    repaired_payload = response.choices[0].message.content or ""
    return _extract_json_object(repaired_payload)


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
    try:
        parsed = _extract_json_object(payload)
    except ValueError as exc:
        try:
            parsed = _repair_json_with_llm(client, payload)
        except Exception:
            debug_path = _save_debug_payload(payload, department)
            raise ValueError(f"{exc} Raw model output saved to {debug_path}") from exc
    return ResumeProfile.model_validate(parsed).model_dump()
