FROM condaforge/mambaforge:4.10.1-0

COPY environment.lock.yml project/environment.lock.yml
RUN mamba env update --name base --file project/environment.lock.yml && conda clean --all --force-pkgs-dir --yes

RUN pip install git+https://github.com/ploomber/ploomber@aws-batch --no-deps

COPY dist/* project/
WORKDIR /project/
# we need to get the config file with credentials
RUN tar --strip-components=1 -zxvf {{filename}}
RUN pip install {{filename}} --no-deps

