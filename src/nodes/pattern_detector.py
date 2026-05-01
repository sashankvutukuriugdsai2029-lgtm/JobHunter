"""
pattern_detector — Detects recurring themes in rejection feedback.
Only triggers if len(feedback_log) >= 3 (business rule).
Uses LLM for clustering with keyword fallback.
"""

from __future__ import annotations

import os
import re
from collections import Counter
from typing import List, Tuple


# Keywords that map to common rejection themes
THEME_KEYWORDS = {
    "System Design": ["system design", "design round", "architecture", "scalability", "distributed systems"],
    "Data Structures & Algorithms": ["algorithm", "data structure", "coding challenge", "leetcode", "dsa"],
    "Frontend Skills": ["react", "frontend", "css", "ui", "hooks", "component"],
    "Backend Skills": ["backend", "api", "database", "server", "microservice"],
    "Communication": ["communication", "culture fit", "team fit", "soft skills", "presentation"],
    "Experience Level": ["experience", "seniority", "years", "overqualified", "underqualified"],
    "Leadership": ["leadership", "management", "lead", "mentoring", "team lead"],
    "Cloud/DevOps": ["aws", "cloud", "devops", "kubernetes", "docker", "infrastructure"],
    "Domain Knowledge": ["domain", "industry", "fintech", "healthcare", "specific knowledge"],
}


def _detect_patterns_keyword(feedback_log: list) -> List[dict]:
    """Keyword-based pattern detection across feedback entries."""
    theme_counts: Counter = Counter()
    theme_reasons: dict = {}

    for event in feedback_log:
        reason = event.get("extracted_reason", "").lower()
        missing_skills = event.get("missing_skills_at_application", [])

        # Track missing skills
        for skill in missing_skills:
            theme = f"{skill} gap"
            theme_counts[theme] += 1
            if theme not in theme_reasons:
                theme_reasons[theme] = []
            theme_reasons[theme].append("Skill gap identified at application")

        # Track text themes
        for theme, keywords in THEME_KEYWORDS.items():
            if any(kw in reason for kw in keywords):
                theme_counts[theme] += 1
                if theme not in theme_reasons:
                    theme_reasons[theme] = []
                theme_reasons[theme].append(event.get("extracted_reason", ""))

    patterns = []
    for theme, count in theme_counts.items():
        is_skill_gap = theme.endswith(" gap")
        source = "skill_gap" if is_skill_gap else "feedback_text"
        
        # Determine source = "both" if it's a known theme mapped to a skill, but for simplicity:
        # A theme is "both" if we detected it via skill gap AND text feedback. 
        # For now, let's just mark it if reason list has both types.
        has_text = any(not r.startswith("Skill gap") for r in theme_reasons[theme])
        has_skill = any(r.startswith("Skill gap") for r in theme_reasons[theme])
        if has_text and has_skill:
            source = "both"

        # Thresholds: >= 3 for text, >= 2 for both or skill gap
        if count >= 3 or (count >= 2 and source in ("skill_gap", "both")):
            if is_skill_gap:
                action = f"Add {theme.replace(' gap', '')} to focus_skills for future jobs"
            elif theme in ("System Design", "Data Structures & Algorithms"):
                action = f"Down-level target seniority to Mid-Level and add {theme} preparation resources"
            elif theme == "Experience Level":
                action = "Adjust target seniority down one level to match market expectations"
            elif theme in ("Frontend Skills", "Backend Skills"):
                action = f"Add {theme.replace(' Skills', '')} courses to prep recommendations and adjust focus areas"
            else:
                action = f"Add {theme} improvement resources to preparation plan"

            patterns.append({
                "theme": theme,
                "occurrences": count,
                "proposed_action": action,
                "source": source,
            })

    return patterns


def _detect_patterns_llm(feedback_log: list) -> List[dict]:
    """Use LLM to cluster rejection reasons into themes."""
    try:
        from src.llm_factory import get_llm
        llm = get_llm(temperature=0.2)

        reasons = "\n".join(
            f"- {e.get('extracted_reason', 'Unknown')}" for e in feedback_log
        )

        prompt = (
            "Analyze these job rejection reasons and identify recurring themes. "
            "For each theme that appears 3 or more times, output EXACTLY in this format:\n"
            "THEME: <theme name>\n"
            "COUNT: <number>\n"
            "ACTION: <proposed strategy change>\n\n"
            f"Rejection reasons:\n{reasons}\n\n"
            "Output themes (only those with 3+ occurrences):"
        )

        response = llm.invoke(prompt)
        text = response.content.strip()

        # Parse LLM output
        patterns = []
        theme_blocks = text.split("THEME:")
        for block in theme_blocks[1:]:  # Skip first empty split
            lines = block.strip().split("\n")
            theme = lines[0].strip()
            count = 3
            action = ""
            for line in lines[1:]:
                if line.strip().startswith("COUNT:"):
                    try:
                        count = int(re.search(r"\d+", line).group())
                    except (AttributeError, ValueError):
                        count = 3
                elif line.strip().startswith("ACTION:"):
                    action = line.replace("ACTION:", "").strip()

            if count >= 3 and theme:
                patterns.append({
                    "theme": theme,
                    "occurrences": count,
                    "proposed_action": action or f"Adjust strategy based on {theme} weakness",
                })

        return patterns if patterns else _detect_patterns_keyword(feedback_log)

    except Exception:
        return _detect_patterns_keyword(feedback_log)


def pattern_detector(state: dict) -> dict:
    """Detect recurring rejection patterns. Only runs if >= 3 feedback events."""
    feedback_log = state.get("feedback_log", [])

    # Business rule: need at least 3 events
    if len(feedback_log) < 3:
        return {"rejection_patterns": [], "strategy_proposal": {}}

    # Check cooling rules — skip patterns whose changes are locked
    strategy = state.get("current_strategy", {})
    locked = set(strategy.get("locked_changes", []))
    positive_since_change = strategy.get("positive_events_since_last_change", 0)

    def is_negative_outcome(reason: str) -> bool:
        text = reason.lower()
        positive_signals = ["offer", "congratulations", "advanced to next interview round", "scheduled for interview"]
        negative_signals = [
            "reject",
            "failed",
            "did not",
            "insufficient",
            "lacked",
            "mismatch",
            "not meet",
            "moved forward with other candidates",
            "position filled",
            "weak",
        ]
        if any(n in text for n in negative_signals):
            return True
        if any(p in text for p in positive_signals):
            return False
        # Default unresolved feedback to negative so we can still learn from it.
        return True

    rejections = [e for e in feedback_log if is_negative_outcome(e.get("extracted_reason", ""))]

    if len(rejections) < 3:
        # We might still have skill gaps!
        patterns = _detect_patterns_keyword(feedback_log)
    else:
        # Try LLM on rejections, fall back to keywords
        patterns_llm = _detect_patterns_llm(rejections)
        patterns_kw = _detect_patterns_keyword(feedback_log)
        
        # Merge them (prefer LLM for text, keep skill_gap from kw)
        merged = {p["theme"]: p for p in patterns_llm}
        for p in patterns_kw:
            if p.get("source") == "skill_gap":
                merged[p["theme"]] = p
            elif p["theme"] in merged:
                # If LLM and keyword found it, maybe it's "both" if one is skill gap
                pass
        patterns = list(merged.values())

    # Filter out locked patterns (unless cooldown expired via positive events)
    active_patterns = []
    for p in patterns:
        theme_key = p["theme"].lower()
        if theme_key in {lc.lower() for lc in locked} and positive_since_change < 3:
            continue  # Still on cooldown
        active_patterns.append(p)

    if active_patterns:
        # Propose the most significant pattern (highest occurrences)
        top_pattern = max(active_patterns, key=lambda p: p["occurrences"])
        return {
            "rejection_patterns": active_patterns,
            "strategy_proposal": top_pattern,
        }

    return {"rejection_patterns": active_patterns, "strategy_proposal": {}}
