set -e

# TODO: give change to pass custom commands
apt-get install g++ --yes
apt-get install gcc --yes

# TODO: add print command to give more context to errors

conda update -n base -c defaults conda

eval "$(conda shell.bash hook)"
conda activate base

cd /mnt/vol1
conda env create --file environment.yml --name env
conda activate env

pip install -r requirements.txt

pip install .


pytest