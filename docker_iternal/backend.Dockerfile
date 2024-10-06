FROM python:slim
LABEL authors="exizman"

WORKDIR /app

COPY ./requirements.txt ./requirements.txt

RUN pip install -r requirements.txt

ENV PYTHONUNBUFFERED=1


ARG MINIO_ENDPOINT
ARG MINIO_ACCESS_KEY
ARG MINIO_SECRET_KEY

ARG POSTGRES_USER
ARG POSTGRES_PASSWORD
ARG POSTGRES_HOST
ARG POSTGRES_PORT
ARG POSTGRES_NAME

ARG KAFKA_BROKERS

ENV MINIO_ENDPOINT=$MINIO_ENDPOINT
ENV MINIO_ACCESS_KEY=$MINIO_ACCESS_KEY
ENV MINIO_SECRET_KEY=$MINIO_SECRET_KEY

ENV POSTGRES_USER=$POSTGRES_USER
ENV POSTGRES_PASSWORD=$POSTGRES_PASSWORD
ENV POSTGRES_HOST=$POSTGRES_HOST
ENV POSTGRES_PORT=$POSTGRES_PORT
ENV POSTGRES_NAME=$POSTGRES_NAME

ENV KAFKA_BROKERS=$KAFKA_BROKERS


COPY ./backend /app/backend
COPY ./db /app/db

ENTRYPOINT ["uvicorn", "backend.run_web:app", "--host", "0.0.0.0", "--port", "8000"]