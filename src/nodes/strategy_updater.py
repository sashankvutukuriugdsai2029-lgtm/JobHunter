"""
strategy_updater - Adjusts the search strategy based on approved patterns.
Only runs after human approval.
"""

from __future__ import annotations

from datetime import datetime


SENIORITY_LEVELS = ["Junior", "Mid-Level", "Senior"]


def _downlevel_seniority(current: str) -> str:
    """Move seniority down one level."""
    current_lower = current.strip().lower()
    for i, level in enumerate(SENIORITY_LEVELS):
        if level.lower() == current_lower and i > 0:
            return SENIORITY_LEVELS[i - 1]
    return current


PREP_RESOURCES = {
    "System Design": [
        "Read 'Designing Data-Intensive Applications' by Martin Kleppmann",
        "Watch System Design Interview channel content",
        "Practice on systemdesign.one or designgurus.io",
    ],
    "Data Structures & Algorithms": [
        "Complete the NeetCode 150 problem set",
        "Read 'Cracking the Coding Interview' by Gayle McDowell",
        "Watch Abdul Bari algorithm lectures",
    ],
    "Frontend Skills": [
        "Review the React Hooks documentation",
        "Build three projects with React and TypeScript",
        "Take a Frontend Masters React course",
    ],
    "Backend Skills": [
        "Read 'Clean Architecture' by Robert Martin",
        "Build one REST API project from scratch",
        "Study backend fundamentals content",
    ],
    "Communication": [
        "Read 'Crucial Conversations'",
        "Practice STAR method responses",
        "Run two mock interview sessions",
    ],
    "Leadership": [
        "Read 'The Manager's Path' by Camille Fournier",
        "Document three leadership examples",
        "Practice staff-level interview questions",
    ],
}


def _uplevel_seniority(current: str) -> str:
    """Move seniority up one level (restoration after positive events)."""
    current_lower = current.strip().lower()
    for i, level in enumerate(SENIORITY_LEVELS):
        if level.lower() == current_lower and i < len(SENIORITY_LEVELS) - 1:
            return SENIORITY_LEVELS[i + 1]
    return current


def strategy_updater(state: dict) -> dict:
    """Apply the approved strategy change and persist an explainable change log.
    
    Also handles Session 3 restoration: if enough positive events have
    accumulated since the last pivot, restore seniority back up one level
    and clear the cooldown lock.
    """
    strategy = dict(state.get("current_strategy", {}))
    proposal = state.get("strategy_proposal", {})
    approved = state.get("strategy_approved", False)

    # ── Session 3: Positive-event restoration ────────────────────
    # If there is no pending approval but positive events have accumulated
    # past the cooldown threshold, restore seniority.
    locked = list(strategy.get("locked_changes", []))
    positive_since_change = strategy.get("positive_events_since_last_change", 0)

    if positive_since_change >= 3 and locked and not approved:
        old_seniority = strategy.get("target_seniority", "Senior")
        new_seniority = _uplevel_seniority(old_seniority)
        changes_made: list[str] = []
        if new_seniority != old_seniority:
            strategy["target_seniority"] = new_seniority
            changes_made.append(
                f"Seniority restored from {old_seniority} to {new_seniority} "
                f"after {positive_since_change} positive events"
            )

        # Clear cooldown locks since the candidate has improved
        cleared = list(locked)
        strategy["locked_changes"] = []
        strategy["positive_events_since_last_change"] = 0
        changes_made.append(f"Cleared cooldown locks: {', '.join(cleared)}")

        strategy_change_log = list(state.get("strategy_change_log", []))
        strategy_change_log.append({
            "date": datetime.now().strftime("%Y-%m-%d"),
            "theme": "Positive Progress — Restoration",
            "proposed_action": "Restore seniority and clear cooldowns based on positive feedback trend",
            "changes": changes_made,
        })

        return {
            "current_strategy": strategy,
            "strategy_change_log": strategy_change_log,
            "strategy_approved": False,
            "strategy_proposal": {},
            "rejection_patterns": [],  # Reset patterns since issue is resolved
        }

    # ── Normal pivot flow (Session 2) ────────────────────────────
    if not approved or not proposal:
        return {}

    theme = proposal.get("theme", "Unknown")
    action = proposal.get("proposed_action", "Adjust strategy based on detected pattern")
    changes_made: list[str] = []

    # 1) Seniority adjustment when explicitly suggested by proposal action.
    action_lower = action.lower()
    if any(token in action_lower for token in ["down-level", "downlevel", "seniority", "adjust target seniority"]):
        old_seniority = strategy.get("target_seniority", "Senior")
        new_seniority = _downlevel_seniority(old_seniority)
        if new_seniority != old_seniority:
            strategy["target_seniority"] = new_seniority
            changes_made.append(f"Target seniority changed from {old_seniority} to {new_seniority}")

    # 2) Prep recommendations are always updated with theme-relevant resources.
    prep = PREP_RESOURCES.get(theme, [f"Study targeted resources for {theme}"])
    existing_prep = strategy.get("prep_recommendations", [])
    new_prep = [p for p in prep if p not in existing_prep]
    strategy["prep_recommendations"] = existing_prep + new_prep
    if new_prep:
        changes_made.append(f"Added {len(new_prep)} preparation recommendation(s) for {theme}")

    # 3) Focus area update for skill patterns.
    focus = list(strategy.get("focus_areas", []))
    focus_skills = list(strategy.get("focus_skills", []))
    derived_focus = theme.replace(" Skills", "")
    
    if action_lower.startswith("add ") and "to focus_skills" in action_lower:
        skill_to_add = theme.replace(" gap", "")
        if skill_to_add not in focus_skills:
            focus_skills.append(skill_to_add)
            strategy["focus_skills"] = focus_skills
            changes_made.append(f"Added '{skill_to_add}' to focus skills")
    elif derived_focus not in focus and theme in ("System Design", "Frontend Skills", "Backend Skills"):
        focus.append(derived_focus)
        strategy["focus_areas"] = focus
        changes_made.append(f"Added '{derived_focus}' to focus areas")

    # 4) Guarantee at least one visible strategy parameter change.
    if not changes_made:
        fallback_note = f"Targeted follow-up for pattern: {theme}"
        strategy["prep_recommendations"] = strategy.get("prep_recommendations", []) + [fallback_note]
        changes_made.append("Added explicit preparation follow-up note")

    # Lock this theme until cooldown is satisfied.
    locked = list(strategy.get("locked_changes", []))
    if theme not in locked:
        locked.append(theme)
    strategy["locked_changes"] = locked
    strategy["positive_events_since_last_change"] = 0

    strategy_change_log = list(state.get("strategy_change_log", []))
    strategy_change_log.append(
        {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "theme": theme,
            "proposed_action": action,
            "changes": changes_made,
        }
    )

    return {
        "current_strategy": strategy,
        "strategy_change_log": strategy_change_log,
        "strategy_approved": False,
        "strategy_proposal": {},
    }
