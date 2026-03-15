"""
LLM service — uses Groq to parse PDFs into structured data.
Only used for admin PDF uploads. Never used for attendance math.
"""

import json
import os
import pdfplumber
from io import BytesIO
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"


def _get_client() -> Groq:
    return Groq(api_key=GROQ_API_KEY)


def extract_pdf_text(pdf_bytes: bytes) -> str:
    """Extract all text from a PDF file."""
    text_parts: list[str] = []
    with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
    return "\n\n".join(text_parts)


def parse_calendar_pdf(pdf_bytes: bytes) -> dict:
    """
    Parse an activity calendar PDF into structured calendar data.

    Returns dict with:
        academic_year: str
        term: str
        start_date: str (YYYY-MM-DD)
        last_working_date: str (YYYY-MM-DD)
        events: list[{name, start_date, end_date, event_type}]
    """
    text = extract_pdf_text(pdf_bytes)
    if not text.strip():
        return {"error": "Could not extract text from PDF"}

    client = _get_client()

    prompt = f"""You are parsing an academic activity calendar. Extract structured data from the following text.

RULES:
1. Identify the academic year (e.g., "2025-2026") and the term/semester name.
2. Identify the start date (first teaching/working date) and last working date.
3. Extract ALL events: holidays, exam periods (CIA, finals), events (sports day, cultural fest), etc.
4. For multi-day events, set both start_date and end_date.
5. Classify each event as: "holiday", "exam", or "event".
6. All dates must be in YYYY-MM-DD format.
7. Return ONLY valid JSON, no other text.

JSON Schema:
{{
  "academic_year": "string",
  "term": "string",
  "start_date": "YYYY-MM-DD",
  "last_working_date": "YYYY-MM-DD",
  "events": [
    {{
      "name": "string",
      "start_date": "YYYY-MM-DD",
      "end_date": "YYYY-MM-DD",
      "event_type": "holiday|exam|event"
    }}
  ]
}}

Calendar text:
---
{text}
---

Return the JSON:"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=4096,
    )

    raw = response.choices[0].message.content.strip()

    # Try to extract JSON from the response
    try:
        # Handle responses wrapped in markdown code blocks
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"error": "Failed to parse LLM response", "raw_response": raw, "extracted_text": text[:500]}


def parse_enrolment_pdf(pdf_bytes: bytes) -> list[dict]:
    """Parse an enrolment PDF."""
    text = extract_pdf_text(pdf_bytes)
    return parse_enrolment_text(text)


def parse_enrolment_text(text: str) -> list[dict]:
    """
    Parse enrolment/timetable text into structured subject data.
    
    Returns list of:
        {
            code: str,
            name: str,
            credits: int,
            category: str,
            offerings: [{
                batch: str,
                slot: str,
                department: str,
                staff: str,
                slots: [{day_of_week: int, start_time: "HH:MM", end_time: "HH:MM", duration_hours: int}]
            }]
        }
    """
    if not text.strip():
        return [{"error": "Provided text is empty"}]

    client = _get_client()

    prompt = f"""You are parsing a course enrolment/timetable text for an engineering college. Extract structured subject and offering data.

RULES:
1. Each subject has a code, name, credits, and category.
2. Each subject may have multiple offerings (different batches/slots/staff).
3. Each offering has weekly meeting times. Convert day names to numbers: Monday=0, Tuesday=1, Wednesday=2, Thursday=3, Friday=4, Saturday=5.
4. Times should be in 24-hour "HH:MM" format.
5. Duration is typically 1 hour. If a class runs 2 consecutive hours, set duration_hours=2.
6. Return ONLY valid JSON array, no other text.

JSON Schema (array of subjects):
[
  {{
    "code": "string",
    "name": "string",
    "credits": integer,
    "category": "string",
    "offerings": [
      {{
        "batch": "string or null",
        "slot": "string or null",
        "department": "string or null",
        "staff": "string or null",
        "slots": [
          {{
            "day_of_week": integer,
            "start_time": "HH:MM",
            "end_time": "HH:MM",
            "duration_hours": integer
          }}
        ]
      }}
    ]
  }}
]

Enrolment text:
---
{text}
---

Return the JSON array:"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=8192,
    )

    raw = response.choices[0].message.content.strip()

    try:
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()
        return json.loads(raw)
    except json.JSONDecodeError:
        return [{"error": "Failed to parse LLM response", "raw_response": raw}]
