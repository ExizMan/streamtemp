import json
import logging
import os
import socket
import sys
from io import BytesIO

import cv2
import requests

#почему то пришлось прибивать
current_dir = os.path.dirname(os.path.realpath(__file__))
root_dir = os.path.abspath(
    os.path.join(current_dir, '..', '..'))  # Assuming minio_client.py is two directories above the current script

# Add the root directory to the Python path
sys.path.append(root_dir)

from utils.minio_client import minio_client

from confluent_kafka import Consumer, KafkaError, KafkaException
from websocket import create_connection

backend_host = os.environ.get('BACKEND_HOST', 'localhost')
backend_port = os.environ.get('BACKEND_PORT', 8000)
backend_domain = f"{backend_host}{':' + str(backend_port) if backend_port else ''}"

kafka_brokers = os.getenv("KAFKA_BROKERS", "localhost:9092")

conf = {
    'bootstrap.servers': kafka_brokers,
    'group.id': 'my_consumer_group',
    'auto.offset.reset': 'earliest'
}

consumer = Consumer(conf)
consumer.subscribe(['video'])


def generate_frames(video_file) -> bytes:
    frame_count = 0
    try:
        with open('temp.mp4', 'wb') as f:
            f.write(video_file)

        video = cv2.VideoCapture('temp.mp4')

        while True:
            ret, frame = video.read()
            if not ret:
                break

            (ret, jpeg) = cv2.imencode(".jpg", frame)
            frame_count += 1
            try:
                pass
            except Exception as e:
                print(f"Ошибка: {e}")
            if ret:
                yield frame_count, [jpeg.tobytes()]
    except Exception as e:
        print(f"Ошибка: {e}")
    finally:
        os.remove('temp.mp4')


def process_video(video_file):
    #TODO yield frame in video_file это пример того, как оно работает
    i = 0
    while i < 100:
        yield i, i
        i += 1
        print(i)
    if i == 100:
        return


# ПОТОМ НОРМ ДОБАВЛЮ
#
# db = psycopg2.connect(
#     host="localhost",
#     database="mydatabase",
#     user="myuser",
#     password="mypassword"
# )

class VideoProcessingActor:

    def __init__(self):
        self.progress = 0
        self.logger = logging.getLogger(__name__)

    #эндпоинта пока нет
    def send_progress(self):
        ws = create_connection(f"ws://{backend_domain}/video_api/ws/progress/")
        ws.send(self.progress)

    @staticmethod
    def send_result(result):
        """
        Для обработки в реальном времени

        """
        ws = create_connection(f"ws://{backend_domain}/video_api/ws/message/")
        ws.send(result)

    @staticmethod
    def send_result_post_request(result):
        req = requests.post(f"http://{backend_domain}/video_api/post_video_from_ml/", data=result)

    def process_message(self, message):
        print(message)

        filename = message

        video_file = minio_client.get_file('localbucket', filename)
        video_data = video_file.get('Body').read()

        print(type(video_file))
        self.progress = 0
        self.result = None

        # поменять в бд состояние

        # TODO запилить логику обработки видео. Это я просто подставли обработку видео для примера
        arr = [frame for frame_num, frame in generate_frames(bytes(video_data))]

        # TODO Здесь отправляется видео целиком
        self.send_result_post_request('some_value')

        # TODO Здесь отправляется видео целиком, локально не храним в системе ничего, так как много пересылаем видео
        minio_client.upload_file('localbucket', self.result, f'processed_{filename}')

        consumer.commit()


running = True


def shutdown():
    running = False


def basic_consume_loop(consumer, topics):
    try:
        consumer.subscribe(topics)

        while running:
            msg = consumer.poll(timeout=1.0)
            if msg is None:
                continue

            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    sys.stderr.write('%% %s [%d] reached end at offset %d\n' %
                                     (msg.topic(), msg.partition(), msg.offset()))
                elif msg.error():
                    raise KafkaException(msg.error())
            else:
                actor = VideoProcessingActor()
                actor.process_message(msg.value().decode('utf-8'))
    finally:
        consumer.close()


if __name__ == '__main__':
    basic_consume_loop(consumer, ['video'])
