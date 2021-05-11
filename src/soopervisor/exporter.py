from soopervisor.enum import Backend
from soopervisor.aws.batch import AWSBatchExporter
from soopervisor.aws.lambda_ import AWSLambdaExporter
from soopervisor.airflow.export import AirflowExporter
from soopervisor.argo.export import ArgoWorkflowsExporter


def for_backend(backend):
    mapping = {
        Backend.aws_batch: AWSBatchExporter,
        Backend.aws_lambda: AWSLambdaExporter,
        Backend.airflow: AirflowExporter,
        Backend.argo_workflows: ArgoWorkflowsExporter,
    }

    if backend not in Backend:
        raise ValueError(f'{backend!r} is not a valid backend')

    return mapping[backend]
