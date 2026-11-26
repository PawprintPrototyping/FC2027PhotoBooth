import pytest
from tbot import send_photo, send_video
from pathlib import Path

@pytest.mark.asyncio
async def test_send_photo_still():
    await send_photo(photo=Path(__file__).parent.resolve() / Path("boykisser.jpg"))


@pytest.mark.asyncio
async def test_send_video():
    await send_video(video=Path(__file__).parent.resolve() / Path("boykisser.gif"))
