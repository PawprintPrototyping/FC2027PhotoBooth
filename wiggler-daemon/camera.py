import typing

from picamera2 import Picamera2
from PIL import Image
from loguru import logger
from config import CONFIG
import pendulum

from pathlib import Path

PHOTOS_LOCATION = CONFIG.artifacts_location / "photos_archive"


def gen_timestamped_filename(extension: str) -> str:
    timestamp = pendulum.now(tz=CONFIG.timezone)
    return f"wiggle_{timestamp.year}-{timestamp.month}-{timestamp.day}_{timestamp.hour}_{timestamp.minute}_{timestamp.second}_{timestamp.microsecond}.{extension}"

async def take_photo(camera_nums: typing.Tuple[int, ...]) -> typing.Tuple[Image, ...]:
    logger.info(f"Taking a photo from cameras {', '.join([str(camera_num) for camera_num in camera_nums])}")
    if len(camera_nums) > 2:
        logger.warning("Taking photos from more than 2 cameras! Something is off")
    cameras: typing.List[Picamera2, ...] = []
    for camera in camera_nums:
        camera_obj = Picamera2(camera_num=camera)
        camera_config = camera_obj.create_still_configuration()
        camera_obj.configure(camera_config=camera_config)
        camera_obj.start()
        cameras.append(camera_obj)
    cameras: typing.Tuple[Picamera2, ...] = tuple(cameras)
    images: typing.List[Image, ...] = []
    for camera in cameras:
        images.append(camera.capture_image("main"))
    return tuple(images)

async def create_gif(photos: typing.Tuple[Image, ...], save_location: Path) -> Path:
    filename = gen_timestamped_filename(extension="gif")
    photos[0].save(
        str(save_location / filename),
        save_all=True,
        append_images=photos[1:],
        duration=10,
        loop=0
    )
    return save_location / filename

async def create_pngs(photos: typing.Tuple[Image, ...], save_location: Path) -> typing.Tuple[Path, ...]:
    filenames: typing.List[Path, ...] = []
    for photo in photos:
        filename = save_location / gen_timestamped_filename(extension="png")
        filenames.append(filename)
        photo.save(
            str(filename)
        )
    return tuple(filenames)