# Exporting to Luigi

Examples to convert Ploomber pipelines into Luigi pipelines. Conversion scrit
at `ploomber_dag.py`

## Setup

```sh
# optional: create virtual env. e.g., if using conda
conda create --name luigi python=3.9 --yes
conda activate luigi

# install packages
pip install ploomber luigi

# optional: install pygraphviz to allow plotting
# note: the simplest way to get pygraphviz working is via conda, for
# alternatives, see this
# https://docs.ploomber.io/en/latest/user-guide/faq_index.html?highlight=pygraphviz#plotting-a-pipeline
conda install pygraphviz -c conda-forge --yes
```

## Running examples

Get one of the examples:

```sh
ploomber examples -n templates/ml-basic -o ml-basic

# optional: plot pipeline (this generates a pipeline.png)
ploomber plot
```

Copy the script:

```sh
cp ploomber_dag.py ml-basic/ploomber_dag.py
```

Run in Luigi:

```sh
cd ml-basic

# install example requirements
pip install -r requirements.txt

# add current directory to pythonpath so luigi can find it
export PYTHONPATH=$(pwd)

# execute
luigi --local-scheduler --module ploomber_dag fit

# check output
ls output
```

Another example:

```sh
ploomber examples -n templates/exploratory-analysis -o eda

# optional: plot pipeline (this generates a pipeline.png)
ploomber plot

cp ploomber_dag.py eda/ploomber_dag.py

cd eda
pip install -r requirements.txt

export PYTHONPATH=$(pwd)
luigi --local-scheduler --module ploomber_dag custom

# check output
ls product
```

A final example, this time using `soorgeon`, to refactor a notebook first:

```sh
# setup
pip install soorgeon scikit-learn matplotlib seaborn
mkdir refactored
cd refactored
wget https://raw.githubusercontent.com/ploomber/soorgeon/main/examples/machine-learning/nb.ipynb

# refactor notebook
soorgeon refactor nb.ipynb
cp ../ploomber_dag.py ploomber_dag.py

# optional: plot pipeline (this generates a pipeline.png)
ploomber plot

# add current directory to pythonpath so luigi can find it
export PYTHONPATH=$(pwd)
luigi --local-scheduler --module ploomber_dag linear_regression

# check output
ls output
```

## Limitations

* Only supports `luigi.LocalTarget` outputs