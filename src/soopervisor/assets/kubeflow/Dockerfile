FROM condaforge/mambaforge:4.10.1-0

# find custom lib and included in PYTHONPATH
{%- set pypath = 'lib/' if lib else 'null' %}

{% if lib %}

ENV PYTHONPATH {{pypath}}

{% endif %}


{%- set name = 'environment.lock.yml' if conda else 'requirements.lock.txt' %}

COPY {{name}} project/{{name}}

{% if conda %}
RUN mamba env update --name base --file project/{{name}} && conda clean --all --force-pkgs-dir --yes
{% else %}
RUN pip install --requirement project/{{name}} && rm -rf /root/.cache/pip/
{% endif %}

COPY dist/* /tmp
WORKDIR /tmp

# extract to get any config files at the root
RUN tar --strip-components=1 -zxvf *.tar.gz

{% if setup_py %}
# install from the source distribution
RUN pip install *.tar.gz --no-deps
{% endif %}
