# sample_project

## File layout

* `pipeline.yaml` - Contains the pipeline's configuration and list of tasks

* `environment.yml` - Project dependencies

* `raw.py`, `clean.py`, `plot.py` - Pipeline tasks
* `output/` - Executed notebooks generate from pipeline tasks and other generated files




## Setup environment

To create your environment with the following command:

```sh
conda env create --file environment.yml
```
Then activate it:

```sh
  conda activate my-project
```


## Execute pipeline

```sh
ploomber entry pipeline.yaml
```

Make sure you execute this command inside your project's root folder (the one that contains the `pipeline.yaml` file).

All output is saved in `output/`.