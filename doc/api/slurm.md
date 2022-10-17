# SLURM

## The `template.sh` file

When using SLURM as backend, the `soopervisor add {env-name}` command wil create an
`{env-name}/template.sh` file.

Under the hood, Soopervisor uses the `template.sh` for all tasks in your
pipeline and executes a `sbatch job.sh` command for each one.

`template.sh` contains two placeholders `{{name}}` and `{{command}}`,
these placeholders are mandatory and should not be removed, at runtime
Soopervisor will replace them with the name of the task and the command
execute, one per task in your pipeline. However, you may add other commands
to `template.sh` to customize execution. Typically, you’ll have to add any
preparation steps, like activating a virtual environment:

```sh
#!/bin/bash
#SBATCH --job-name={{name}}
#SBATCH --output=result.out
#

# activate conda environment
conda activate myenv
# execute task
srun {{command}}
```

## Customizing task execution

You may want to use different settings for each task in your
pipeline in some scenarios. To achieve that, you can add more files next to the
`template.sh` file, and Soopervisor will choose which one to use depending
on the task’s name.

The resolution logic is as follows. Say you have a task named `fit-gpu`:


1. Look for an exact match (i.e., `fit-gpu.sh`)


2. Look for a file with a double underscore placeholder (e.g., `fit-__.sh`, or `__-gpu.sh`)


3. If no matches, use `template.sh`

You can use this templating feature to customize the submitted jobs, for example
to pass custom parameters to the `srun` command.
