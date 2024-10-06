import os

from fastapi import UploadFile
from sqlalchemy import select

from backend.video import schemas
from db.models import video
from sqlalchemy.ext.asyncio import AsyncSession
from backend.utils.minio_client import minio_client
from confluent_kafka import Producer








# async def generate_frames(rtsp_url: str, camera_id: str) -> bytes:
#     frame_count = 0
#     try:
#
#         video = cv2.VideoCapture(rtsp_url, apiPreference=cv2.CAP_FFMPEG)
#         while True:
#             ret, frame = video.read()
#             if not ret:
#                 break
#
#             (ret, jpeg) = cv2.imencode(".jpg", frame)
#             frame_count += 1
#             try:
#                 pass
#             except Exception as e:
#                 print(f"Ошибка: {e}")
#             if ret:
#                 yield jpeg.tobytes()
#     except Exception as e:
#         print(f"Ошибка: {e}")


async def get_rtsp_url(camera_id: str, db: AsyncSession):
    result = await db.execute(select(video.Camera.threadURL).where(video.Camera.id == camera_id))
    rtsp_url = result.scalar()
    return rtsp_url


async def add_camera(camera: schemas.CameraCreate, db: AsyncSession):
    db_camera = video.Camera(
        threadURL=camera.threadURL
    )
    await db_camera.save(db)

    return db_camera

async def add_video(video_file: UploadFile, db: AsyncSession):
    kafka_brokers = os.getenv("KAFKA_BROKERS", "kafka:9092")




    print(os.getenv("KAFKA_BROKERS"))
    kafka_producer = Producer({
        'bootstrap.servers': kafka_brokers,
        'broker.address.family': 'v4'# Update with your Kafka broker address
    })
    file_contents = await video_file.read()
    file_name = video_file.filename
    file_type = video_file.content_type
    file_size = len(file_contents)

    path = minio_client.upload_file('localbucket', file_contents, file_name)
    db_video = video.Video(
        path=path[1],
        state="NonHandled",
        content_type=file_type,
        content_length=file_size
    )
    kafka_producer.produce('video', value=path[1].encode('utf-8'))
    kafka_producer.flush()
    return db_video

async def add_video_from_ml(video_name: str, db: AsyncSession):
    db_video = await db.get(video.Video, video_name)
    if db_video is None:
        raise ValueError(f"Видео '{video_name}' не найдено в базе данных")
    db_video.state = "SUCCESSFUL"
    await db_video.save(db)
    return db_video


async def update_video_state(camera: schemas.CameraCreate, db: AsyncSession):
    db_camera = await db.get(video.Camera, camera.id)
    db_camera.threadURL = camera.threadURL
    await db_camera.save(db)

    return db_camera




async def get_cameras(db: AsyncSession):
    cameras = await db.execute(
        select(video.Camera)
    )
    cameras = cameras.scalars().all()

    return cameras