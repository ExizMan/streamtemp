from fastapi.responses import StreamingResponse
from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.websockets import WebSocket

from db.database import get_db
from backend.video import schemas
from backend.video import services

router = APIRouter(
    prefix="/video_api",
    tags=["video_api"],
    responses={404: {"description": "Not found"}},
)



@router.get("/stream_rtsp/{camera_id}")
async def stream_rtsp(
        camera_id: str,
        db: AsyncSession = Depends(get_db)
):
    #rtsp_url = "rtsp://807e9439d5ca.entrypoint.cloud.wowza.com:1935/app-rC94792j/068b9c9a_stream2"
    rtsp_url = await services.get_rtsp_url(camera_id, db)
    return StreamingResponse(services.generate_frames(rtsp_url=rtsp_url, camera_id=camera_id), media_type="multipart/x-mixed-replace; boundary=frame", status_code=206)



@router.post("/post_camera")
async def post_camera(
        camera: schemas.CameraCreate,
        db: AsyncSession = Depends(get_db)
):
    return await services.add_camera(camera=camera, db=db)

@router.get("/get_cameras", response_model=list[schemas.CameraCreate])
async def get_cameras(
        db: AsyncSession = Depends(get_db)
):
    return await services.get_cameras(db=db)

@router.post("/post_video")
async def post_video(
        video: UploadFile = File(...),
        db: AsyncSession = Depends(get_db)
):
    return await services.add_video(video_file=video, db=db)

@router.post("/post_video_from_ml")
async def post_video_from_ml(
        video_name: str,
        db: AsyncSession = Depends(get_db)):
    return await services.add_video_from_ml(video_file=video_name, db=db)


@router.websocket("/ws/message/")
async def websocket_output(websocket: WebSocket):
    print("check")
    await websocket.accept()
    try:
        while True:
            message = await websocket.receive_text()
            print(message)
            await websocket.send_text(f"Message text was: {message}")
    except Exception as e:
        print(f"Ошибка в вебсокете: {e}")
    finally:
        await websocket.close()



# @router.websocket("/ws/{camera_id}")
# async def websocket_video_stream(websocket: WebSocket, camera_id: str, db: AsyncSession = Depends(get_db)):
#
#     await websocket.accept()
#     rtsp_url = await services.get_rtsp_url(camera_id, db)
#     print(rtsp_url)
#     for frame in services.generate_frames(rtsp_url=rtsp_url, camera_id=camera_id):
#         try:
#             await websocket.send_bytes(frame)
#             await asyncio.sleep(1/30)
#         except Exception as e:
#             print(f"Ошибка при отправке кадра: {e}")
#             await websocket.close()
#             break


