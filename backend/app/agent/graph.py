from langgraph.graph import END, START, StateGraph

from app.agent.nodes import (
    evaluate_report_node,
    execute_tools_node,
    generate_charts_node,
    generate_report_node,
    load_task_node,
    match_fields_node,
)
from app.agent.state import AnalysisGraphState
from app.storage.analysis_store import get_task_state


def route_on_task_status(state: AnalysisGraphState) -> str:
    return "failed" if state.get("status") == "failed" else "continue"


def build_analysis_graph():
    graph = StateGraph(AnalysisGraphState)
    graph.add_node("load_task", load_task_node)
    graph.add_node("match_fields", match_fields_node)
    graph.add_node("execute_tools", execute_tools_node)
    graph.add_node("generate_charts", generate_charts_node)
    graph.add_node("generate_report", generate_report_node)
    graph.add_node("evaluate_report", evaluate_report_node)

    graph.add_edge(START, "load_task")
    graph.add_edge("load_task", "match_fields")
    graph.add_conditional_edges(
        "match_fields",
        route_on_task_status,
        {
            "continue": "execute_tools",
            "failed": END,
        },
    )
    graph.add_conditional_edges(
        "execute_tools",
        route_on_task_status,
        {
            "continue": "generate_charts",
            "failed": END,
        },
    )
    graph.add_edge("generate_charts", "generate_report")
    graph.add_edge("generate_report", "evaluate_report")
    graph.add_edge("evaluate_report", END)

    return graph.compile()


def run_analysis_graph(task_id: str) -> dict:
    state = get_task_state(task_id)
    if state is None:
        raise ValueError(f"Task {task_id} not found")

    graph = build_analysis_graph()
    return graph.invoke(state)
