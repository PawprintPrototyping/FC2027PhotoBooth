import typing
from abc import ABC, abstractmethod
from asyncio import Event, wait_for, TimeoutError, subprocess, sleep
from loguru import logger
import time

class Controller(ABC):
    """
    Message passing infrastructure between an external camera controller and the actual camera itself. The camera and
    the controller use this to communicate when a photo should be taken, a reboot is requested, etc.
    """

    def __init__(self):
        self._photo_request = Event()
        self._ping_request = Event()
        self._pong = Event()

        self._took_first_photo = Event()
        self._took_second_photo = Event()
        self._photo_preprocessing = Event()
        self._printing_photo = Event()
        self._converted_to_gif = Event()
        self._uploaded = Event()
        self._ready_for_new_photo = Event()

    async def _clear_camera_states(self):
        self._took_first_photo.clear()
        self._took_second_photo.clear()
        self._photo_preprocessing.clear()
        self._printing_photo.clear()
        self._converted_to_gif.clear()
        self._uploaded.clear()

    async def not_ready_for_photo(self):
        self._ready_for_new_photo.clear()

    async def ready_for_photo(self):
        self._ready_for_new_photo.set()

    async def took_first_photo(self):
        self._took_first_photo.set()

    async def took_second_photo(self):
        self._took_second_photo.set()

    async def photo_preprocessing(self):
        self._photo_preprocessing.set()

    async def printing_photo(self):
        self._printing_photo.set()

    async def converted_to_gif(self):
        self._converted_to_gif.set()

    async def uploaded_photo(self):
        self._uploaded.set()

    @abstractmethod
    async def main_loop(self):
        ...

    async def request_photo(self) -> bool:
        """
        Controller requests the camera to take a photo and start the conversion + upload process
        :return: True on success, False on failure
        """
        if not self._ready_for_new_photo.is_set():
            logger.error("Cannot take a new photo, the camera is not ready yet")
            return False
        self._photo_request.set()
        return True

    async def photo_requested(self) -> bool:
        """
        Camera polls this to determine if the controller has requested a photo. If the controller has requested a photo,
        consume the event and reset it.
        :return: True if it has, False if it has not.
        """

        if self._photo_request.is_set():
            self._photo_request.clear()
            return True
        return False

    async def ping(self, timeout: int = 5) -> True:
        """
        Controller requests a ping from the camera loop.
        :return: True if the camera pongs back, false if it does not pong back within some timeout
        """
        self._ping_request.set()
        start_time = time.time()
        logger.info(f"Pinging camera loop, waiting for {timeout}s...")
        try:
            await wait_for(self._pong.wait(), timeout=timeout)
        except TimeoutError:
            logger.error(f"Camera loop did not respond with a pong within {timeout}s")
            # Conservatively clean up event flags
            self._pong.clear()
            self._ping_request.clear()
            return False
        self._pong.clear()
        self._ping_request.clear()
        logger.success(f"Camera loop responded to a ping in {time.time() - start_time:.2f}s")
        return True

    async def pong(self) -> None:
        """
        Camera loop pongs back within a certain amount of time. This should NOT be called from within the controller
        loop
        :return: Nothing, just pong back
        """
        if self._ping_request.is_set():
            self._pong.set()
            self._ping_request.clear()

    @staticmethod
    async def request_reboot() -> None:
        """
        Reboot the PC. This is going to require that the user has sudoers permission to run the reboot command
        :return: Nothing, this should kill the interpreter
        """
        reboot_proc = await subprocess.create_subprocess_exec("sudo reboot",
                                                              stdout=subprocess.PIPE,
                                                              stderr=subprocess.PIPE)
        try:
            await wait_for(reboot_proc.communicate(), timeout=10)
        except TimeoutError as e:
            reboot_proc.kill()
            raise TimeoutError("Timed out while waiting for the reboot command to finish") from e
        raise RuntimeError(f"The reboot was not successful. Got return code {reboot_proc.returncode} stderr="
                           f"{reboot_proc.stderr.read()}, stdout={reboot_proc.stdout.read()}")
