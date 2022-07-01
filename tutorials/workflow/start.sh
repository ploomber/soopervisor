set -e
set -x

# copy sample notebook
ls
ls /mnt/shared-folder/
cp /nb.ipynb /mnt/shared-folder/nb.ipynb
cp /requirements.lock.txt /mnt/shared-folder/requirements.lock.txt

# copy sample data
INPUT=/mnt/shared-folder/input
mkdir -p $INPUT
cp /train.csv $INPUT/train.csv
cp /test.csv $INPUT/test.csv

# create cluster
k3d cluster delete mycluster
k3d cluster create mycluster --volume $SHARED_DIR:/host #--port 2746:2746

# install argo
kubectl create ns argo
kubectl apply -n argo -f argo-pns.yaml

# start jupyter
# jupyter lab --port 8888 --allow-root --app-dir /mnt & > /jupyterlab.log &2>1

cd /mnt/shared-folder/

/bin/bash