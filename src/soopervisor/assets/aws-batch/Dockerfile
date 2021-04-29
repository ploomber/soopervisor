FROM continuumio/miniconda3

COPY environment.lock.yml project/environment.lock.yml
RUN conda env update --file project/environment.lock.yml

RUN pip install git+https://github.com/ploomber/ploomber@dev

COPY dist/* project/
WORKDIR /project/
RUN tar --strip-components=1 -zxvf {{filename}}
RUN pip install {{filename}}
