"""
Loading dags
"""
from ploomber.constants import TaskStatus
from ploomber.spec import DAGSpec


def load_tasks(incremental=False):
    """Load tasks names and their upstream dependencies

    Parameters
    ----------
    incremental : bool, default=False
        If True, returned dictionary only returns tasks whose status
        is not Skipped

    Returns
    -------
    task : dict
        A dictionary with tasks (keys) and upstream dependencies (values)
        to submit

    args : list
        A list of arguments to pass to "ploomber task {name}"
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
