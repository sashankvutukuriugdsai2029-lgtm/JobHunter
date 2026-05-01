"""
Profile creation and document-ingestion utilities.
Supports creating user profiles from uploaded CV/job documents with optional Gemini parsing.
"""

from __future__ import annotations

import json
import os
import re
from io import BytesIO
from typing import Any


DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
DEMO_PROFILES_PATH = os.path.join(DATA_DIR, "demo_profiles.json")
USER_PROFILES_PATH = os.path.join(DATA_DIR, "user_profiles.json")

TEXT_EXTENSIONS = {
    ".txt",
    ".md",
    ".csv",
    ".json",
    ".yaml",
    ".yml",
    ".log",
    ".rst",
}

SKILL_KEYWORDS = [
    "python",
    "java",
    "javascript",
    "typescript",
    "react",
    "node.js",
    "node",
    "aws",
    "docker",
    "kubernetes",
    "postgresql",
    "mysql",
    "mongodb",
    "rest api",
    "graphql",
    "system design",
    "microservices",
    "django",
    "flask",
    "spring",
    "terraform",
    "ci/cd",
    "git",
]


def _empty_store() -> dict[str, dict[str, Any]]:
    return {"profiles": {}, "default_strategies": {}}


def _ensure_store_shape(data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    if not isinstance(data, dict):
        return _empty_store()
    data.setdefault("profiles", {})
    data.setdefault("default_strategies", {})
    return data


def _slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
    return slug or "candidate"


def _seniority_from_years(years: int) -> str:
    if years <= 2:
        return "Junior"
    if years <= 5:
        return "Mid-Level"
    return "Senior"


def _extract_skills_keyword(text: str) -> list[str]:
    text_lower = text.lower()
    hits = []
    for skill in SKILL_KEYWORDS:
        if skill in text_lower:
            hits.append(skill.title() if skill != "ci/cd" else "CI/CD")
    # Preserve order while deduping.
    unique = []
    seen = set()
    for skill in hits:
        if skill not in seen:
            seen.add(skill)
            unique.append(skill)
    return unique


def _extract_salary_keyword(text: str) -> str:
    """
    Best-effort salary extraction from free text.
    Examples: "$180k", "180000", "120k-150k", "INR 30 LPA".
    """
    if not text:
        return ""
    patterns = [
        r"(\$\s?\d{2,3}(?:,\d{3})?(?:\s?[kK])?(?:\s?-\s?\$?\s?\d{2,3}(?:,\d{3})?(?:\s?[kK])?)?)",
        r"((?:usd|inr|eur)\s?\d[\d,]*(?:\s?-\s?\d[\d,]*)?)",
        r"(\d{2,3}\s?[kK](?:\s?-\s?\d{2,3}\s?[kK])?)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return ""


def _default_strategy(seniority: str, base_skills: list[str]) -> dict[str, Any]:
    return {
        "target_seniority": seniority,
        "focus_areas": base_skills[:3],
        "prep_recommendations": [],
        "locked_changes": [],
        "positive_events_since_last_change": 0,
    }


def _strip_json_fence(content: str) -> str:
    cleaned = content.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?", "", cleaned).strip()
        cleaned = re.sub(r"```$", "", cleaned).strip()
    return cleaned


def _extract_text_from_pdf(file_bytes: bytes) -> str:
    try:
        from PyPDF2 import PdfReader
    except Exception:
        return ""

    try:
        reader = PdfReader(BytesIO(file_bytes))
        pages = [page.extract_text() or "" for page in reader.pages]
        return "\n".join(pages).strip()
    except Exception:
        return ""


def _extract_upload_text(uploaded_file: Any) -> tuple[str, str]:
    """
    Returns:
      (text, warning_message)
    """
    name = getattr(uploaded_file, "name", "uploaded_file")
    ext = os.path.splitext(name)[1].lower()
    raw = uploaded_file.getvalue()

    if ext in TEXT_EXTENSIONS:
        return raw.decode("utf-8", errors="ignore"), ""

    if ext == ".pdf":
        text = _extract_text_from_pdf(raw)
        if text:
            return text, ""
        return "", f"Could not parse PDF text from {name} (install PyPDF2 or upload as .txt)."

    return "", f"Unsupported file type for text extraction: {name}"


def _llm_extract_profile(
    *,
    raw_context: str,
    fallback_name: str,
    fallback_role: str,
    fallback_years: int,
    fallback_salary: str,
    api_key: str,
) -> dict[str, Any] | None:
    if not api_key:
        return None

    try:
        from src.llm_factory import get_llm
        llm = get_llm(temperature=0.1)

        prompt = (
            "Extract a structured candidate profile from the context below.\n"
            "Return JSON only (no prose) with keys:\n"
            "name (string), target_role (string), years_experience (int),\n"
            "base_skills (array of strings), preferred_job_types (array of strings),\n"
            "target_salary (string).\n"
            "Limit base_skills to 20 concrete technical/professional skills.\n\n"
            f"Fallback name: {fallback_name}\n"
            f"Fallback role: {fallback_role}\n"
            f"Fallback years: {fallback_years}\n\n"
            f"Fallback salary: {fallback_salary}\n\n"
            f"Context:\n{raw_context[:14000]}"
        )

        response = llm.invoke(prompt)
        content = _strip_json_fence(response.content if hasattr(response, "content") else str(response))
        parsed = json.loads(content)
        if isinstance(parsed, dict):
            return parsed
        return None
    except Exception:
        return None


def load_all_profiles() -> dict[str, dict[str, Any]]:
    with open(DEMO_PROFILES_PATH, "r", encoding="utf-8") as handle:
        demo = _ensure_store_shape(json.load(handle))

    if os.path.exists(USER_PROFILES_PATH):
        with open(USER_PROFILES_PATH, "r", encoding="utf-8") as handle:
            user = _ensure_store_shape(json.load(handle))
    else:
        user = _empty_store()

    merged_profiles = dict(demo["profiles"])
    merged_profiles.update(user["profiles"])
    merged_strategies = dict(demo["default_strategies"])
    merged_strategies.update(user["default_strategies"])

    return {"profiles": merged_profiles, "default_strategies": merged_strategies}


def create_or_update_user_profile(
    *,
    name: str,
    target_role: str,
    years_experience: int,
    target_salary: str,
    additional_notes: str,
    uploaded_files: list[Any],
    gemini_api_key: str = "",
) -> tuple[str, dict[str, Any], dict[str, Any], list[str]]:
    warnings: list[str] = []
    effective_api_key = (gemini_api_key or os.environ.get("GOOGLE_API_KEY", "")).strip()

    extracted_docs: list[str] = []
    for uploaded in uploaded_files:
        text, warning = _extract_upload_text(uploaded)
        if text.strip():
            extracted_docs.append(f"FILE: {uploaded.name}\n{text.strip()[:8000]}")
        elif warning:
            warnings.append(warning)

    combined_context = "\n\n".join(extracted_docs + [additional_notes.strip()])
    llm_profile = _llm_extract_profile(
        raw_context=combined_context,
        fallback_name=name,
        fallback_role=target_role,
        fallback_years=years_experience,
        fallback_salary=target_salary,
        api_key=effective_api_key,
    )

    keyword_skills = _extract_skills_keyword(combined_context)
    llm_skills = llm_profile.get("base_skills", []) if llm_profile else []

    merged_skills = []
    for skill in llm_skills + keyword_skills:
        skill_str = str(skill).strip()
        if skill_str and skill_str not in merged_skills:
            merged_skills.append(skill_str)

    final_name = str(llm_profile.get("name", "")).strip() if llm_profile else ""
    final_role = str(llm_profile.get("target_role", "")).strip() if llm_profile else ""
    final_years = llm_profile.get("years_experience", years_experience) if llm_profile else years_experience
    final_salary = str(llm_profile.get("target_salary", "")).strip() if llm_profile else ""
    try:
        final_years = int(final_years)
    except Exception:
        final_years = years_experience

    salary_fallback = target_salary.strip() or _extract_salary_keyword(combined_context)

    profile = {
        "name": final_name or name.strip(),
        "base_skills": merged_skills[:20],
        "target_role": final_role or target_role.strip(),
        "years_experience": max(0, final_years),
        "target_salary": final_salary or salary_fallback,
        "notes": additional_notes.strip(),
    }

    seniority = _seniority_from_years(profile["years_experience"])
    strategy = _default_strategy(seniority, profile["base_skills"])

    profile_key = f"{_slugify(profile['name'])}_user"

    if os.path.exists(USER_PROFILES_PATH):
        with open(USER_PROFILES_PATH, "r", encoding="utf-8") as handle:
            user_store = _ensure_store_shape(json.load(handle))
    else:
        user_store = _empty_store()

    user_store["profiles"][profile_key] = profile
    user_store["default_strategies"][profile_key] = strategy

    with open(USER_PROFILES_PATH, "w", encoding="utf-8") as handle:
        json.dump(user_store, handle, indent=2)

    if not llm_profile:
        warnings.append("Gemini extraction unavailable; used keyword and manual inputs.")
    if not profile["base_skills"]:
        warnings.append("No skills extracted. Add more detail in notes or upload a text/PDF resume.")

    return profile_key, profile, strategy, warnings


def save_profile_edits(profile_key: str, updated_profile: dict[str, Any]):
    """Update an existing profile directly and save to disk."""
    if os.path.exists(USER_PROFILES_PATH):
        with open(USER_PROFILES_PATH, "r", encoding="utf-8") as handle:
            user_store = _ensure_store_shape(json.load(handle))
    else:
        user_store = _empty_store()

    if profile_key in user_store["profiles"]:
        # Update existing user profile
        user_store["profiles"][profile_key].update(updated_profile)
    else:
        # It might be a demo profile being edited. We need to copy the full profile first.
        all_profs = load_all_profiles()
        full_prof = all_profs["profiles"].get(profile_key, {})
        user_store["profiles"][profile_key] = full_prof
        user_store["profiles"][profile_key].update(updated_profile)
        
        # Ensure it has a strategy if it's new to user_store
        seniority = _seniority_from_years(user_store["profiles"][profile_key].get("years_experience", 0))
        strategy = all_profs["default_strategies"].get(profile_key) or _default_strategy(seniority, user_store["profiles"][profile_key].get("base_skills", []))
        user_store["default_strategies"][profile_key] = strategy

    with open(USER_PROFILES_PATH, "w", encoding="utf-8") as handle:
        json.dump(user_store, handle, indent=2)
