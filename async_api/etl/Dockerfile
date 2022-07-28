FROM python:3.10

RUN mkdir /etl
WORKDIR /etl

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
COPY ./requirements.txt requirements.txt

RUN  pip install --upgrade pip && pip install -r requirements.txt

COPY . .

ENTRYPOINT ["python3", "etl.py"]
