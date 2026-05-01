"""
feedback_parser - Processes rejection/offer/interview feedback.
Uses LLM to extract a 1-sentence reason from raw text.
Falls back to keyword extraction if LLM is unavailable.
"""

from __future__ import annotations

import os
import re
from datetime import datetime


def _extract_reason_keyword_fallback(raw_text: str) -> str:
    """Simple keyword-based extraction when LLM is unavailable."""
    text_lower = raw_text.lower()

    patterns = {
        "system design": "Candidate lacked system design skills",
        "design round": "Failed the system design interview round",
        "coding challenge": "Did not pass the coding challenge",
        "culture fit": "Not a culture fit for the team",
        "experience": "Insufficient experience for the role",
        "seniority": "Seniority level mismatch",
        "communication": "Communication skills need improvement",
        "technical": "Technical skills did not meet requirements",
        "react": "Lacked required React/frontend experience",
        "python": "Insufficient Python experience",
        "leadership": "Did not demonstrate leadership ability",
        "competitive": "More competitive candidates were selected",
        "salary": "Salary expectations did not align",
        "relocated": "Position was relocated or filled internally",
        "offer accepted": "Candidate received and accepted an offer",
        "congratulations": "Candidate received an offer",
        "next round": "Candidate advanced to next interview round",
        "schedule.*interview": "Candidate scheduled for interview",
    }

    for pattern, reason in patterns.items():
        if re.search(pattern, text_lower):
            return reason

    return "Position filled - moved forward with other candidates"


def _extract_reason_llm(raw_text: str) -> str:
    """Use LLM to extract a 1-sentence rejection reason."""
    try:
        from src.llm_factory import get_llm
        llm = get_llm(temperature=0.1)

        prompt = (
            "You are parsing a job application feedback email. "
            "Extract the PRIMARY reason for rejection (or outcome) in exactly ONE sentence. "
            "If it's an offer or interview invitation, state that clearly. "
            "If the reason is unclear, say 'Position filled - moved forward with other candidates'. "
            f"\n\nEmail text:\n{raw_text[:1000]}\n\nOne-sentence reason:"
        )

        response = llm.invoke(prompt)
        reason = response.content.strip()
        return reason if reason else _extract_reason_keyword_fallback(raw_text)

    except Exception:
        return _extract_reason_keyword_fallback(raw_text)


def feedback_parser(state: dict) -> dict:
    """Parse pending feedback text and create FeedbackEvent entries."""
    pending_text = state.get("pending_feedback_text", "")
    if not pending_text or not pending_text.strip():
        return {}

    feedback_log = list(state.get("feedback_log", []))
    applications = list(state.get("applications", []))

    # Split by --- separator to handle multiple feedback entries.
    raw_entries = [t.strip() for t in pending_text.split("---") if t.strip()]

    for raw_text in raw_entries:
        extracted_reason = _extract_reason_llm(raw_text)
        now_str = datetime.now().strftime("%Y-%m-%d")

        reason_lower = extracted_reason.lower()
        if any(w in reason_lower for w in ["offer", "congratulations", "accepted"]):
            new_status = "offer"
        elif any(w in reason_lower for w in ["interview", "next round", "schedule"]):
            new_status = "interviewing"
        elif any(w in reason_lower for w in ["screening", "phone screen", "recruiter"]):
            new_status = "screening"
        else:
            new_status = "rejected"

        # Attach feedback to the most recent in-flight application.
        target_app_id = ""
        for i in range(len(applications) - 1, -1, -1):
            app = applications[i]
            if app.get("status") in ("applied", "screening", "interviewing"):
                target_app_id = app.get("job_id", "")
                applications[i] = dict(app)
                applications[i]["status"] = new_status
                applications[i]["date_last_updated"] = now_str
                if new_status in ("rejected", "offer"):
                    applications[i]["date_outcome"] = now_str
                break

        feedback_event = {
            "application_id": target_app_id,
            "raw_email_text": raw_text[:500],
            "extracted_reason": extracted_reason,
            "date_logged": now_str,
        }
        feedback_log.append(feedback_event)

    return {
        "feedback_log": feedback_log,
        "applications": applications,
        "pending_feedback_text": "",
    }
