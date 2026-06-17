from app.agent.graph import run_analysis_graph


def run_analysis_task(task_id: str) -> dict:
    return run_analysis_graph(task_id)
