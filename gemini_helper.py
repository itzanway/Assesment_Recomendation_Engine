"""
Thin wrapper around the Gemini API for generating explanations.

You must set the GEMINI_API_KEY environment variable with a valid key from
Google AI Studio / Gemini console.
"""

import os
from typing import List, Dict

import requests


GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GEMINI_GENERATE_URL = (
    "https://generativelanguage.googleapis.com/v1beta/"
    "models/gemini-1.5-flash:generateContent"
)


def _ensure_api_key() -> str:
    api_key = GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY environment variable is not set. "
            "Please export your Gemini API key before using this feature."
        )
    return api_key


def generate_explanation(query_text: str, recommendations: List[Dict]) -> str:

    api_key = _ensure_api_key()

    lines = []
    lines.append("You are an assistant that explains assessment recommendations.")
    lines.append("User query or job description:")
    lines.append(query_text.strip())
    lines.append("")
    lines.append("Recommended SHL assessments:")
    for idx, rec in enumerate(recommendations, start=1):
        name = rec.get("name", "")
        url = rec.get("url", "")
        desc = rec.get("description", "")
        lines.append(f"{idx}. {name}")
        if url:
            lines.append(f"   URL: {url}")
        if desc:
            lines.append(f"   Description: {desc}")
    lines.append("")
    lines.append(
        "Explain in 3–5 concise bullet points why these assessments are a good fit "
        "for this query. Focus on skills, competencies, and use cases."
    )

    prompt = "\n".join(lines)

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt},
                ]
            }
        ]
    }

    resp = requests.post(
        GEMINI_GENERATE_URL,
        params={"key": api_key},
        json=payload,
        timeout=20,
    )
    resp.raise_for_status()
    data = resp.json()
    try:
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError):
        # Fallback: return raw JSON string if parsing fails
        return str(data)


