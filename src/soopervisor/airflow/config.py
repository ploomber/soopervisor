from soopervisor.base.config import ScriptConfig
from soopervisor.base import validate as validate_base
from soopervisor.airflow import validate as validate_airflow


class AirflowConfig(ScriptConfig):
    # TODO: Airflow-exclusive parameters, which operator to use (bash,
    # docker, kubernetespod). Maybe template? jinja template where ploomber's
    # code will be generated, in case there is some customization to do for
    # default parameters

    # TODO: some default values should change. for example, look by default
    # for an environment.lock.yml (explain why) and do not set a default
    # to products. lazy_import=True, allow_incremental=False
    lazy_import: bool = True

    # NOTE: another validation we can implement would be to create the
    # environment.yml and then make sure we can instantiate the dag, this would
    # allow to verify missing dependencies before exporting rather than when
    # trying to run it in the airflow host
    def validate(self):
        d = self.dict()
        dag = validate_base.project(d)
        validate_airflow.pre(d, dag)
