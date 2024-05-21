FROM python:3.12-slim

RUN apt-get update \
    && apt-get -y install libpq-dev gcc

WORKDIR /app
COPY ./ /app

RUN pip install poetry
RUN python3 -m poetry config virtualenvs.create false
RUN python3 -m poetry install

EXPOSE 80
CMD ["uvicorn", "kyotsu.api.main:app", "--host", "0.0.0.0", "--port", "80"]
