"""
Loading dags
"""
from ploomber.constants import TaskStatus
from ploomber.spec import DAGSpec


def load_dag(incremental=False):
    """
    Load DAG and return task names and dependencies in a dictionary

    Parameters
    ----------
    incremental : bool, default=False
        If True, returned dictionary only returns tasks whose status
        is not Skipped
    """
    dag = DAGSpec.find().to_dag()
    dag.render(remote=True)

    tasks = []
    out = {}

    for name, task in dag.items():
        if not incremental or task.exec_status != TaskStatus.Skipped:
            tasks.append(name)

    for t in tasks:
        out[t] = [name for name in dag[t].upstream.keys() if name in tasks]

    return out
