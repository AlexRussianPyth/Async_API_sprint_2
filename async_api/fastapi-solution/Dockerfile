FROM python:3.10

COPY ./requirements.txt .

RUN  pip install --upgrade pip && pip install -r requirements.txt

COPY /src /src

WORKDIR /src
RUN chmod +x entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["./entrypoint.sh"]