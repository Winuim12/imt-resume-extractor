EXTRACTION_SYSTEM_PROMPT = """
You extract structured information from resumes.

Rules:
- Return valid JSON only.
- Do not invent facts.
- If a field is missing, return null or an empty list.
- Normalize obvious formatting issues.
- Infer the candidate's department based on the selected target department and the resume content.
- Keep responsibilities and skills concise.
"""


def build_extraction_prompt(raw_text: str, department: str) -> str:
    return f"""
Target department: {department}

Extract the resume into this JSON schema:
{{
  "candidate_name": string | null,
  "email": string | null,
  "phone": string | null,
  "location": string | null,
  "department": string | null,
  "summary": string | null,
  "total_experience_years": number | null,
  "skills": string[],
  "tools": string[],
  "certifications": string[],
  "education": [
    {{
      "degree": string | null,
      "institution": string | null,
      "graduation_year": string | null
    }}
  ],
  "experience": [
    {{
      "title": string | null,
      "company": string | null,
      "duration": string | null,
      "responsibilities": string[]
    }}
  ],
  "projects": [
    {{
      "name": string | null,
      "description": string | null,
      "technologies": string[]
    }}
  ]
}}

Resume text:
\"\"\"
{raw_text}
\"\"\"
"""


def build_qa_prompt(question: str, context: str) -> str:
    return f"""
Answer the question using only the resume context below.
If the answer is not supported by the context, say that clearly.
Give a concise answer and mention supporting evidence.

Question:
{question}

Context:
{context}
"""
