from dotenv import load_dotenv
load_dotenv()

import os
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver
import sqlite3

from state import JobHunterState, create_fresh_state
from nodes.state_loader import state_loader
from nodes.job_fetcher import job_fetcher
from nodes.matcher import matcher
from nodes.ranker import ranker
from nodes.application_tracker import application_tracker
from nodes.feedback_parser import feedback_parser
from nodes.pattern_detector import pattern_detector
from nodes.strategy_updater import strategy_updater
from nodes.state_saver import state_saver

def build_graph():
    """
    Builds and compiles the JobHunter LangGraph.
    Returns compiled graph with SqliteSaver checkpointer.
    """
    # Create the graph with JobHunterState as state schema
    builder = StateGraph(JobHunterState)

    # Add all 9 nodes
    builder.add_node("state_loader", state_loader)
    builder.add_node("job_fetcher", job_fetcher)
    builder.add_node("matcher", matcher)
    builder.add_node("ranker", ranker)
    builder.add_node("application_tracker", application_tracker)
    builder.add_node("feedback_parser", feedback_parser)
    builder.add_node("pattern_detector", pattern_detector)
    builder.add_node("strategy_updater", strategy_updater)
    builder.add_node("state_saver", state_saver)

    # Set entry point
    builder.set_entry_point("state_loader")

    # Connect nodes in order with edges
    builder.add_edge("state_loader", "job_fetcher")
    builder.add_edge("job_fetcher", "matcher")
    builder.add_edge("matcher", "ranker")
    builder.add_edge("ranker", "application_tracker")
    builder.add_edge("application_tracker", "feedback_parser")
    builder.add_edge("feedback_parser", "pattern_detector")
    builder.add_edge("pattern_detector", "strategy_updater")
    builder.add_edge("strategy_updater", "state_saver")
    builder.add_edge("state_saver", END)

    # Create SQLite checkpointer for persistence
    # This is what makes the agent remember across sessions
    DB_PATH = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), 
        "jobhunter.db"
    )
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    checkpointer = SqliteSaver(conn)

    # Compile with checkpointer
    graph = builder.compile(checkpointer=checkpointer)
    return graph


def run_graph(input_state: dict, thread_id: str = "default") -> dict:
    """
    Runs the graph with given input state.
    thread_id identifies the user session — same thread_id 
    means same user, so state is loaded from previous session.
    Returns the final state as a dict.
    """
    graph = build_graph()

    config = {"configurable": {"thread_id": thread_id}}

    result = graph.invoke(input_state, config=config)
    return result

def get_user_state(thread_id: str) -> dict:
    """
    Fetches the existing state for a user from the checkpointer
    without running the graph. Returns None if no history exists.
    """
    graph = build_graph()
    config = {"configurable": {"thread_id": thread_id}}
    state_snapshot = graph.get_state(config)
    if state_snapshot and state_snapshot.values:
        return state_snapshot.values
    return None


if __name__ == "__main__":
    print("Testing JobHunter graph...")
    print("Running Session 1 (cold start)...")

    # Session 1 input — fresh start
    # candidate_profile will be None (set via UI in real app)
    fresh = create_fresh_state()
    input_dict = fresh.model_dump()

    result = run_graph(input_dict, thread_id="test_user_1")

    print(f"\nSession 1 Results:")
    print(f"  Sessions count: {result.get('sessions_count')}")
    print(f"  Jobs recommended: "
          f"{len(result.get('recommended_jobs', []))}")
    print(f"  Session summary: {result.get('session_summary')}")
    
    seniority = "unknown"
    if result.get('current_strategy'):
        if isinstance(result.get('current_strategy'), dict):
            seniority = result.get('current_strategy').get('seniority_level', 'unknown')
        else:
            seniority = getattr(result.get('current_strategy'), 'seniority_level', 'unknown')
    print(f"  Seniority: {seniority}")

    print("\nGraph built and running correctly!")
    print("jobhunter.db created in project folder OK")
