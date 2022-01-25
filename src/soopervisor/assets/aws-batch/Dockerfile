FROM condaforge/mambaforge:4.10.1-0

{%- set name = 'environment.lock.yml' if conda else 'requirements.lock.txt' %}

COPY {{name}} project/{{name}}

{% if conda %}
RUN mamba env update --name base --file project/{{name}} && conda clean --all --force-pkgs-dir --yes
{% else %}
RUN pip install --requirement project/{{name}} && rm -rf /root/.cache/pip/
{% endif %}

COPY dist/* project/
WORKDIR /project/

# extract to get any config files at the root
RUN tar --strip-components=1 -zxvf *.tar.gz
RUN cp -r /project/ploomber/ /root/.ploomber/  || echo 'ploomber home does not exist'

{% if setup_py %}
# install from the source distribution
RUN pip install *.tar.gz --no-deps
{% endif %}
