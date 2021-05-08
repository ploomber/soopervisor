from enum import Enum, unique, EnumMeta


class EnumContains(EnumMeta):
    def __contains__(cls, item):
        try:
            cls(item)
        except ValueError:
            return False
        else:
            return True


@unique
class Backend(Enum, metaclass=EnumContains):
    aws_batch = 'aws-batch'
    aws_lambda = 'aws-lambda'
    argo_workflows = 'argo-workflows'
    airflow = 'airflow'

    @classmethod
    def __contains__(cls, item):
        try:
            cls(item)
        except ValueError:
            return False
        else:
            return True

    @classmethod
    def get_values(cls):
        return [v.value for v in cls.__members__.values()]
