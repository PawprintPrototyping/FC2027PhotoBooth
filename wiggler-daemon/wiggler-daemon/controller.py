import logging
import typing
from .camera import take_photo, create_gif, create_pngs
from .config import CONFIG
from .tbot import send_photo, send_video
from .stats import STATISTICS
from asyncio import Event, wait_for, TimeoutError, subprocess, TaskGroup

class Mailbox:
    """
    One way communication mailbox, blocking. Client requests data, can block on the mailbox (poll to check its state)
    and the server returns data and a boolean to represent success
    """
    def __init__(self):
        # Flag to represent when the client wants data. While set, mailbox is busy
        self._client_wants_data: Event = Event()
        self._data: typing.Optional[str] = None
        self._returncode: typing.Optional[bool] = None

    # Client Functions
    async def request_data(self) -> bool:
        if self.busy():
            logging.error("Client is requesting data from mailbox, but mailbox is still busy")
            return False
        self._client_wants_data.set()
        # Clear out the old data from the mailbox
        self._returncode = None
        self._data = None
        return True

    async def busy(self) -> bool:
        return self._client_wants_data.is_set()

    @property
    def data(self) -> typing.Optional[str]:
        if self._data is None:
            logging.error("Client is trying to read data from an empty mailbox")
        return self._data

    @property
    def returncode(self) -> typing.Optional[str]:
        if self._returncode is None:
            logging.error("Client is trying to read a returncode from an empty mailbox")
        return self._returncode

    # Server Functions
    async def client_wants_data(self):
        return self.busy()

    async def return_value(self, data: str, returncode: bool):
        self._data = data
        self._returncode = returncode
        self._client_wants_data.clear()


class Controller:
    """
    Message passing infrastructure between an external camera controller and the actual camera itself. The camera and
    the controller use this to communicate when a photo should be taken, a reboot is requested, etc.
    """

    def __init__(self):
        # States that the controller can be in
        self._took_photos = Event()
        self._photo_preprocessing = Event()
        self._printing_photo = Event()
        self._converted_to_gif = Event()
        self._uploaded = Event()
        self._ready_for_new_photo = Event()

        # Stop the various polling loops
        self._running = Event()

        # Mailboxes for sending data between controller and external
        self.stats_mailbox = Mailbox()
        self.photo_mailbox = Mailbox()
        self.reboot_mailbox = Mailbox()

    async def _clear_controller_states(self):
        self._took_photos.clear()
        self._photo_preprocessing.clear()
        self._printing_photo.clear()
        self._converted_to_gif.clear()
        self._uploaded.clear()
        self._ready_for_new_photo.clear()

    async def get_state_string(self) -> str:
        return (f"Took Photos: {'1' if self._took_photos.is_set() else '0'}\n"
                f"Photo Processed: {'1' if self._photo_preprocessing.is_set() else '0'}\n"
                f"Printed Photo: {'1' if self._printing_photo.is_set() else '0'}\n"
                f"Converted Photo: {'1' if self._converted_to_gif.is_set() else '0'}\n"
                f"Uploaded: {'1' if self._uploaded.is_set() else '0'}\n"
                f"Ready For New Photo: {'1' if self._ready_for_new_photo.is_set() else '0'}\n")

    async def main_loop(self):
        self._running.set()
        async with TaskGroup() as tg:
            tg.create_task(self._photo_loop())
            tg.create_task(self._stats_loop())
            tg.create_task(self._reboot_loop())

    async def stop(self):
        self._running.clear()

    async def _photo_loop(self):
        while self._running.is_set():
            if self.photo_mailbox.client_wants_data():
                success = await self._take_photo()
                await self.photo_mailbox.return_value(data="Took Photo!" if success else "Did not take photo", returncode=success)

    async def _stats_loop(self):
        while self._running.is_set():
            if self.stats_mailbox.client_wants_data():
                stats = await STATISTICS.get_statistics()
                state = self.get_state_string()
                await self.photo_mailbox.return_value(data=f"{stats}\n{state}",
                                                      returncode=True)

    async def _reboot_loop(self):
        while self._running.is_set():
            if self.reboot_mailbox.client_wants_data():
                await self._request_reboot()
                # Above should kill the entire machine. If it continues, it failed
                await self.reboot_mailbox.return_value(data="Reboot failed", returncode=False)

    async def _take_photo(self) -> bool:
        """
        Camera polls this to determine if the controller has requested a photo. If the controller has requested a photo,
        consume the event and reset it.
        :return: True if it has, False if it has not.
        """
        if self._ready_for_new_photo.is_set():
            self._ready_for_new_photo.clear()
            photos = await take_photo(camera_nums=CONFIG.cameras)
            self._took_photos.set()
            await STATISTICS.took_photo()
            png_locations = await create_pngs(photos=photos, save_location=CONFIG.artifacts_location)
            self._photo_preprocessing.set()
            gif_location = await create_gif(photos=photos, save_location=CONFIG.artifacts_location)
            self._converted_to_gif.set()
            await send_video(video=gif_location)
            for png_location in png_locations:
                await send_photo(photo=png_location)
            self._uploaded.set()
            await self._clear_controller_states()
            self._ready_for_new_photo.set()
            return True
        return False

    @staticmethod
    async def _request_reboot() -> None:
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
