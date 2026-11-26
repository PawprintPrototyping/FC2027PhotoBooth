import pytest
from camera import take_photo, create_gif
from config import CONFIG
from tbot import send_video

@pytest.mark.asyncio
async def test_photo_pipeline():
    photos = await take_photo(camera_nums=(0, 1))
    gif_file = await create_gif(photos=photos, save_location=CONFIG.artifacts_location)
    await send_video(video=gif_file)
