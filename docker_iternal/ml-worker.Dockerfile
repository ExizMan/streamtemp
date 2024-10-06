FROM python:slim
LABEL authors="exizman"

WORKDIR /app

COPY ./requirements.txt ./requirements.txt
RUN apt-get update && apt-get install ffmpeg libsm6 libxext6  -y

RUN pip install -r requirements.txt


ARG MINIO_ENDPOINT
ARG MINIO_ACCESS_KEY
ARG MINIO_SECRET_KEY

ENV MINIO_ENDPOINT=$MINIO_ENDPOINT
ENV MINIO_ACCESS_KEY=$MINIO_ACCESS_KEY
ENV MINIO_SECRET_KEY=$MINIO_SECRET_KEY



COPY ./ml-worker ./ml-worker




ENTRYPOINT ["python"]
CMD ["ml-worker/worker_entrypoint.py"]