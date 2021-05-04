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

    @classmethod
    def __contains__(cls, item):
        try:
            cls(item)
        except ValueError:
            return False
        else:
            return True
