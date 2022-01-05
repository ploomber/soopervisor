import subprocess

# NOTE: to_testing_files_from_path depends the latest version of docutils
# but sphinx or airflow may try to downgrade it. If you get the
# AttributeError: 'Values' object has no attribute 'tab_width error, upgrade
# docutils
from pkgmt.testing.docker import to_testing_files_from_path


def test_argo_tutorial(tmp_empty, root_path):
    subprocess.check_call(['k3d', 'cluster', 'delete', 'mycluster'])
    subprocess.check_call(['rm', '-rf', '$HOME/ploomber-k8s'])

    to_testing_files_from_path(root_path / 'doc' / 'tutorials' /
                               '_k8s-local.rst')

    subprocess.check_call(['bash', 'test.sh'])


def test_airflow_tutorial(tmp_empty, root_path):
    subprocess.check_call(['k3d', 'cluster', 'delete', 'mycluster'])
    subprocess.check_call(['rm', '-rf', '$HOME/ploomber-airflow'])

    to_testing_files_from_path(root_path / 'doc' / 'tutorials' / 'airflow.rst')

    subprocess.check_call(['bash', 'test.sh'])
