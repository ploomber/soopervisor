FROM public.ecr.aws/lambda/python:3.8

COPY app.py   ./
COPY dist/*   ./
RUN pip install *.whl
CMD ["app.handler"]
