"""
Export a Ploomber DAG to Kubeflow
"""
import os
from pathlib import Path

import click

from ploomber.io._commander import Commander, CommanderStop
from soopervisor.kubeflow.config import KubeflowConfig
from soopervisor import commons
from soopervisor import abc


class KubeflowExporter(abc.AbstractExporter):
    CONFIG_CLASS = KubeflowConfig

    @staticmethod
    def _add(cfg, env_name):
        """Export Ploomber project to Kubeflow

        Generates a .py file that exposes a dag variable
        """
        click.echo('Exporting to Kubeflow...')

        # TODO: modify Dockerfile depending on package or non-package
        with Commander(workspace=env_name,
                       templates_path=('soopervisor', 'assets')) as e:
            e.copy_template('kubeflow/Dockerfile',
                            conda=Path('environment.lock.yml').exists(),
                            setup_py=Path('setup.py').exists())

    @staticmethod
    def _validate(cfg, dag, env_name):
        """
        Validates a project before exporting as an Kubeflow DAG.
        This runs as a sanity check in the development machine
        """
        pass

    @staticmethod
    def _export(cfg, env_name, mode, until, skip_tests, ignore_git,
                lazy_import):
        """
        Copies the current source code to the target environment folder.
        The code along with the DAG declaration file can be copied to
        KUBEFLOW_HOME for execution
        """
        with Commander(workspace=env_name,
                       templates_path=('soopervisor', 'assets')) as e:
            tasks, args = commons.load_tasks(cmdr=e, name=env_name, mode=mode)
            dag, relative_path = commons.load_dag(cmdr=e,
                                                  name=env_name,
                                                  mode=mode,
                                                  lazy_import=lazy_import)
            products_list = {}

            # TODO deal with the second mode.
            for name, task in dag.items():
                product = task.product
                products_list[name] = []
                try:
                    product.items()
                    products = product.products.products
                    for item in products:
                        products_list[name].append(
                            {item: str(Path(products[item]).resolve())})
                except AttributeError:  # Single product
                    products_list[name].append(str(Path(product).resolve()))

            if not tasks:
                raise CommanderStop(f'Loaded DAG in {mode!r} mode has no '
                                    'tasks to submit. Try "--mode force" to '
                                    'submit all tasks regardless of status')

            pkg_name, target_image = commons.docker.build(
                e,
                cfg,
                env_name,
                until=until,
                entry_point=args[1],
                skip_tests=skip_tests,
                ignore_git=ignore_git)

            print("Generating kubeflow script")
            generate_kubeflow_script(tasks, args, products_list, target_image,
                                     pkg_name, env_name)

            print("Compiling to a kubeflow yaml")
            output_path = f'{env_name}/kubeflow_pipeline.yaml'
            os.system(f"python kubeflow_pipeline.py {output_path}")

            click.echo(f'Done. Saved kubeflow yaml to {output_path!r}')
            click.echo(
                'Submit your workflow through:\n'
                '1. Direct upload to cluster\n'
                '2. Client API call: client.create_run_from_pipeline_package('
                f'{output_path}, arguments=None)')


def _make_kubeflow_dag(name, dependencies, command):
    dag_task = {
        "name": name,
        "template": name,
    }

    if dependencies:
        dag_task['dependencies'] = dependencies
        dag_task['arguments'] = {'artifacts': []}
        for dependency in dependencies:
            dag_task['arguments']['artifacts'].append({
                'name':
                f'{dependency}-product',
                'from':
                '{{tasks.' + dependency + '.outputs.artifacts.' + dependency +
                '-product}}'
            })

    return dag_task


def _parse_task_dependencies(tasks, dependencies, products, task_name):
    headers = []
    args = []

    # Parse task inputs
    if dependencies:
        headers.append('inputs:\n')

        for dependency in dependencies:
            headers.append('- {name: ' + dependency + '}\n')

    # Parse task outputs
    task_products = products[task_name]
    if task_products:
        headers.append('outputs:\n')
        args.append('        args:\n')
        if len(task_products) == 1:
            headers.append('- {name: product}\n')
            args.append('        - {outputPath: product}\n')
        else:
            for product in task_products:
                key = list(product.keys())[0]
                headers.append('- {name: ' + key + '}\n')
                args.append('        - {outputPath: ' + key + '}\n')

    return args, headers


def _parse_pipeline_task(tasks, dependencies, products, task_name):
    pipeline = []
    if dependencies:
        pipeline.append(f'  {task_name}_step = {task_name}(\n')

        if len(dependencies) == 1:  # No ending comma
            item = dependencies[0]
            pipeline.append(f'      {item}_step.outputs["product"]\n')
            pipeline.append('   )\n\n')
        else:
            ctr = 0
            for item in dependencies:
                item_products = products[item]
                if len(item_products) == 1:
                    pipeline.append(f'      {item}_step.outputs["product"]')
                else:
                    for product in item_products:
                        key = list(product.keys())[0]
                        pipeline.append(f'      {item}_step.outputs["{key}"]')
                if ctr != len(dependencies) - 1:
                    pipeline.append(',\n')
                else:
                    pipeline.append('\n')
                ctr += 1
            pipeline.append('   )\n\n')
    else:
        pipeline.append(f'  {task_name}_step = {task_name}()\n\n')

    return pipeline


def _parse_pipeline_tasks(tasks, target_image, products, args, pkg_name):
    tasks_lines = []
    pipeline_lines = []
    for task_name, upstream in tasks.items():
        # Make sure if the task has an underscore it's converted to dash
        command = f'ploomber task {task_name.replace("_", "-")}'

        if args:
            command = f'{command} {" ".join(args)}'

        # Write task definition and text content
        tasks_lines.append(
            f'{task_name} = comp.load_component_from_text("""\n')
        tasks_lines.append(f'name: {task_name}\n')

        # Deal with task inputs outputs
        kubeflow_args, dependency_lines = _parse_task_dependencies(
            tasks, upstream, products, task_name)
        if dependency_lines:
            tasks_lines += dependency_lines

        tasks_lines.append('implementation:\n')
        tasks_lines.append('    container:\n')
        tasks_lines.append(f'        image: {target_image}\n')
        tasks_lines.append('        command:\n')
        tasks_lines.append('        - sh\n')
        tasks_lines.append('        - -c\n')
        tasks_lines.append('        - |\n')
        for index in range(0, len(kubeflow_args) - 1):
            tasks_lines.append(f'          mkdir -p "$(dirname "${index}")"\n')
        tasks_lines.append(f'          {command}\n')

        # Deal with output/input kubeflow_args
        if kubeflow_args:
            tasks_lines += kubeflow_args

        tasks_lines.append('""")\n\n')

        pipeline_lines += _parse_pipeline_task(tasks, upstream, products,
                                               task_name)

    # Create the pipeline
    tasks_lines.append('# Define your pipeline\n')
    tasks_lines.append(f'def {pkg_name}():\n')
    tasks_lines += pipeline_lines
    tasks_lines.append('\n')

    return tasks_lines


def filter_dict(tasks, to_replace, replace_with):
    new_tasks = {}
    for k, v in tasks.items():
        new_k = None
        if "-" in k:
            new_k = k.replace(to_replace, replace_with)
        else:
            new_k = k
        new_v = []
        for key in v:
            if "-" in key:
                new_v.append(key.replace(to_replace, replace_with))
            else:
                new_v.append(key)
        new_tasks[new_k] = new_v

    return new_tasks


def generate_kubeflow_script(tasks, args, products, target_image, pkg_name,
                             env_name):
    """
    Generates a dictionary with the spec used by Kubeflow to construct the
    DAG and pipeline.yaml
    """

    # Make sure tasks/producs/pkg_name doesn't contain dashes
    tasks = filter_dict(tasks, "-", "_")
    products = {k.replace('-', '_'): v for k, v in products.items()}
    pkg_name = pkg_name.replace('-', '_')
    fname = 'kubeflow_pipeline.py'

    try:
        with open(fname, 'w') as f:

            # Initialize imports
            f.write('import kfp\n')
            f.write('import kfp.components as comp\n')
            f.write('import kfp.compiler as compiler\n\n')
            f.write('# Put your KFP cluster endpoint URL here if working from'
                    ' GCP notebooks (or local notebooks). '
                    '("https://xxxxx.notebooks.googleusercontent.com/")\n')
            f.write('#kfp_endpoint="YOUR_KFP_ENDPOINT"\n')
            f.write('#client = kfp.Client(kfp_endpoint)\n\n')
            f.write('# This is a sanity check to make sure your notebook and'
                    ' cluster can communicate\n')
            f.write('#print(client.list_experiments())\n\n')

            # Parse single pipeline tasks
            f.writelines(
                _parse_pipeline_tasks(tasks, target_image, products, args,
                                      pkg_name))

            # API call to submit the pipeline
            f.write('# Compile, and submit this pipeline for execution.\n')
            f.write(f'pipeline_name = "{pkg_name}"\n')
            f.write(f'compiler.Compiler().compile({pkg_name}, '
                    'f"ploomber_pipeline.yaml")\n')
            f.write(f'#client.create_run_from_pipeline_func({pkg_name}, '
                    'arguments={})\n')
    except FileExistsError:
        print(f"Trying to write to an existing file, please remove"
              f" {fname} and retry")
