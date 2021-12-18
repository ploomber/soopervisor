from enum import Enum, unique, EnumMeta


class CustomEnum(EnumMeta):
    def __contains__(cls, item):
        try:
            cls(item)
        except ValueError:
            return False
        else:
            return True


@unique
class Backend(Enum, metaclass=CustomEnum):
    aws_batch = 'aws-batch'
    aws_lambda = 'aws-lambda'
    argo_workflows = 'argo-workflows'
    airflow = 'airflow'
    slurm = 'slurm'

    @classmethod
    def get_values(cls):
        return [v.value for v in cls.__members__.values()]


@unique
class Mode(Enum, metaclass=CustomEnum):
    incremental = 'incremental'
    regular = 'regular'
    force = 'force'

    @classmethod
    def get_values(cls):
        return [v.value for v in cls.__members__.values()]
