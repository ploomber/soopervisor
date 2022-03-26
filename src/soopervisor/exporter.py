from soopervisor.enum import Backend
from soopervisor.aws.batch import AWSBatchExporter, CloudExporter
from soopervisor.aws.lambda_ import AWSLambdaExporter
from soopervisor.airflow.export import AirflowExporter
from soopervisor.kubeflow.export import KubeflowExporter
from soopervisor.argo.export import ArgoWorkflowsExporter
from soopervisor.shell.export import SlurmExporter


def for_backend(backend):
    """Returns an Exporter class given the backend string identifier

    Parameters
    ----------
    backend : str
        Backend string identifier
    """
    mapping = {
        Backend.aws_batch: AWSBatchExporter,
        Backend.aws_lambda: AWSLambdaExporter,
        Backend.airflow: AirflowExporter,
        Backend.kubeflow: KubeflowExporter,
        Backend.argo_workflows: ArgoWorkflowsExporter,
        Backend.slurm: SlurmExporter,
        Backend.cloud: CloudExporter,
    }

    if backend not in Backend:
        raise ValueError(f'{backend!r} is not a valid backend')

    return mapping[backend]
