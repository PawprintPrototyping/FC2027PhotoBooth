from picamzero import Camera

from pathlib import Path

DEFAULT_PHOTOS_LOCATION = Path.home() / "photos_archive"

class CameraWiggler:
    cam = Camera()