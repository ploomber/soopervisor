from pathlib import Path
from unittest.mock import Mock, ANY

import yaml
import pytest

from soopervisor.kubeflow.export import KubeflowExporter, commons


# Test the task output is same as it's product
@pytest.mark.skip(reason="incompatibility with kfp version")
@pytest.mark.parametrize(
    "mode, args",
    [
        ["incremental", ""],
        ["regular", ""],
        ["force", " --force"],
    ],
    ids=["incremental", "regular", "force"],
)
def test_export(
    monkeypatch,
    mock_docker_my_project,
    backup_packaged_project,
    no_sys_modules_cache,
    skip_repo_validation,
    mode,
    args,
):
    load_tasks_mock = Mock(wraps=commons.load_tasks)
    monkeypatch.setattr(commons, "load_tasks", load_tasks_mock)

    exporter = KubeflowExporter.new(path_to_config="soopervisor.yaml", env_name="serve")

    exporter.add()
    exporter.export(mode=mode, until=None)

    yaml_str = Path("serve/ploomber_pipeline.yaml").read_text()
    spec = yaml.safe_load(yaml_str)
    # dag = DAGSpec.find().to_dag()

    load_tasks_mock.assert_called_once_with(cmdr=ANY, name="serve", mode=mode)

    # print(yaml_str)
    total_dag_size = len(spec["spec"]["templates"])

    # Get dag by pipeline name
    dag = [
        template["dag"]
        for template in spec["spec"]["templates"]
        if "my-project" in template["name"]
    ][0]
    tasks = dag["tasks"]

    get_task = [
        template for template in spec["spec"]["templates"] if "get" in template["name"]
    ][0]

    cmd = "ploomber task get --entry-point " + str(
        Path("src", "my_project", "pipeline.yaml")
    )

    assert total_dag_size - 1 == len(tasks)
    assert set(spec) == {"apiVersion", "kind", "metadata", "spec"}
    assert "generateName" in set(spec["metadata"])
    assert {"entrypoint", "templates"}.issubset(set(spec["spec"]))

    container_cmd = get_task["container"]["command"][2]
    assert cmd in container_cmd
    if args:
        assert args in container_cmd
    assert get_task["container"]["image"] == "your-repository/name:0.1dev"
    assert spec["metadata"]["generateName"] == "my-project-"
