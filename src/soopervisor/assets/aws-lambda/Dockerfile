FROM public.ecr.aws/lambda/python:3.8

COPY requirements.lock.txt .
RUN pip install --requirement requirements.lock.txt

COPY dist/*   .
RUN pip install *.whl --no-deps

COPY app.py   .

CMD ["app.handler"]
