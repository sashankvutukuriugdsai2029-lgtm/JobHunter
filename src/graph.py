"""
JobHunter LangGraph State Machine.

Graph flow:
  state_loader → job_fetcher → matcher → ranker → application_tracker
    → (if feedback exists) feedback_parser → pattern_detector
    → (if pattern found, INTERRUPT) strategy_updater → job_fetcher (re-rank)
    → state_saver → END
"""

from __future__ import annotations

import os
import sqlite3

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, StateGraph

from src.models import JobHunterState
from src.nodes.state_loader import state_loader
from src.nodes.job_fetcher import job_fetcher
from src.nodes.matcher import matcher
from src.nodes.ranker import ranker
from src.nodes.application_tracker import application_tracker
from src.nodes.feedback_parser import feedback_parser
from src.nodes.pattern_detector import pattern_detector
from src.nodes.strategy_updater import strategy_updater
from src.nodes.state_saver import state_saver


# ---------------------------------------------------------------------------
# Routing functions
# ---------------------------------------------------------------------------

def should_parse_feedback(state: dict) -> str:
    """Route to feedback_parser if there's pending feedback text.
    Also route to strategy_updater directly if approval is pending
    or if positive events have accumulated enough for seniority restoration."""
    pending = state.get("pending_feedback_text", "")
    approved = state.get("strategy_approved", False)
    proposal = state.get("strategy_proposal", {})
    strategy = state.get("current_strategy", {})

    if pending and pending.strip():
        return "feedback_parser"
    # If approval is pending from a previous session, go directly to strategy_updater
    if approved and proposal and proposal.get("theme"):
        return "strategy_updater"
    # Session 3 restoration: positive events accumulated past cooldown threshold
    locked = strategy.get("locked_changes", [])
    positive_since = strategy.get("positive_events_since_last_change", 0)
    if positive_since >= 3 and locked:
        return "strategy_updater"
    return "state_saver"


def should_update_strategy(state: dict) -> str:
    """Route to strategy_updater if a pattern was found and approved."""
    proposal = state.get("strategy_proposal", {})
    approved = state.get("strategy_approved", False)

    if proposal and proposal.get("theme"):
        if approved:
            return "strategy_updater"
        # Pattern found but not yet approved — go to state_saver
        # The UI will handle the interrupt / approval flow
        return "state_saver"
    return "state_saver"


def after_strategy_update(state: dict) -> str:
    """After strategy update, re-fetch jobs with new criteria."""
    return "job_fetcher_refetch"


# ---------------------------------------------------------------------------
# Graph builder
# ---------------------------------------------------------------------------

def build_graph(db_path: str | None = None) -> tuple:
    """
    Build and compile the JobHunter state graph with SqliteSaver persistence.

    Returns:
        (compiled_graph, checkpointer_connection)
    """
    # Set up SQLite checkpointer
    if db_path is None:
        checkpoint_dir = os.path.join(os.path.dirname(__file__), "..", "checkpoints")
        os.makedirs(checkpoint_dir, exist_ok=True)
        db_path = os.path.join(checkpoint_dir, "jobhunter.db")

    conn = sqlite3.connect(db_path, check_same_thread=False)
    memory = SqliteSaver(conn)

    # Build the graph
    builder = StateGraph(JobHunterState)

    # Add all 9 required nodes
    builder.add_node("state_loader", state_loader)
    builder.add_node("job_fetcher", job_fetcher)
    builder.add_node("matcher", matcher)
    builder.add_node("ranker", ranker)
    builder.add_node("application_tracker", application_tracker)
    builder.add_node("feedback_parser", feedback_parser)
    builder.add_node("pattern_detector", pattern_detector)
    builder.add_node("strategy_updater", strategy_updater)
    builder.add_node("state_saver", state_saver)

    # Add a re-fetch node (same function, different name for the cycle)
    builder.add_node("job_fetcher_refetch", job_fetcher)
    builder.add_node("matcher_refetch", matcher)
    builder.add_node("ranker_refetch", ranker)

    # Define edges
    builder.set_entry_point("state_loader")

    # Main flow: state_loader → job_fetcher → matcher → ranker → application_tracker
    builder.add_edge("state_loader", "job_fetcher")
    builder.add_edge("job_fetcher", "matcher")
    builder.add_edge("matcher", "ranker")
    builder.add_edge("ranker", "application_tracker")

    # After tracking apps, check for feedback or pending approval
    builder.add_conditional_edges(
        "application_tracker",
        should_parse_feedback,
        {
            "feedback_parser": "feedback_parser",
            "strategy_updater": "strategy_updater",
            "state_saver": "state_saver",
        },
    )

    # After parsing feedback, detect patterns
    builder.add_edge("feedback_parser", "pattern_detector")

    # After pattern detection, check if strategy should update
    builder.add_conditional_edges(
        "pattern_detector",
        should_update_strategy,
        {
            "strategy_updater": "strategy_updater",
            "state_saver": "state_saver",
        },
    )

    # After strategy update, re-fetch jobs with new criteria
    builder.add_edge("strategy_updater", "job_fetcher_refetch")
    builder.add_edge("job_fetcher_refetch", "matcher_refetch")
    builder.add_edge("matcher_refetch", "ranker_refetch")
    builder.add_edge("ranker_refetch", "state_saver")

    # End
    builder.add_edge("state_saver", END)

    # Compile with checkpointer
    graph = builder.compile(checkpointer=memory)

    return graph, conn
