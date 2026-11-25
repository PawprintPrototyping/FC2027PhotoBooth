from __future__ import annotations

import typing
from ipaddress import IPv4Address

import aiohttp
import pendulum
import time
from pathlib import Path
import asyncio
import json
from attr import define
import socket
from loguru import logger
from config import CONFIG

@define
class Statistics:
    start_time: pendulum.DateTime
    up_time: pendulum.duration
    total_photos: int
    photos_this_session: int
    network_ping_rtt: int
    public_ip_address: typing.Optional[IPv4Address]
    local_ip_address: IPv4Address


class StatisticsController:

    PUBLIC_IP_ENDPOINT: str = "https://ipconfig.io"
    STATS_LOCATION: Path = CONFIG.artifacts_location / "wiggler_statistics.json"

    def __init__(self, file_location: Path = STATS_LOCATION):
        self._file_location = file_location
        # Initialize the total photos count
        if not self._file_location.is_dir():
            raise FileExistsError(f"Statistics file {self._file_location} exists and is a directory, cannot continue")
        if StatisticsController.STATS_LOCATION.exists():
            try:
                total_photos = json.loads(self._file_location.read_text())["total_photos"]
            except json.decoder.JSONDecodeError:
                logger.error(f"Stats file at {self._file_location} is corrupted, erasing. Body text is "
                             f"currently: \n {self._file_location.read_text()}")
                self._file_location.unlink(missing_ok=False)
                total_photos = 0
        else:
            logger.info(f"Statistics file {self._file_location} does not exist, starting fresh")
            total_photos = 0

        self._stats = Statistics(
            start_time=pendulum.now(tz=CONFIG.timezone),
            up_time=0,
            total_photos=total_photos,
            photos_this_session=0,
            network_ping_rtt=-1,
            public_ip_address=None,
            local_ip_address=self.get_local_ip(),
        )
    
    @staticmethod
    def get_local_ip() -> IPv4Address:
        """
        Get the IP of the camera PCs local interface
        """
        return IPv4Address(socket.gethostbyname_ex(socket.gethostname()))

    @staticmethod
    async def get_public_ip(timeout: int = 10) -> typing.Tuple[typing.Optional[IPv4Address], typing.Optional[float]]:
        """
        Get the IP of the camera PCs public interface. This requires dialing out to an IP service. Returns None on
        timeout
        :param timeout: How long to wait, in seconds, before giving up trying to get an IP
        :return: The public IP if we have one, else none
        """
        start_time = time.time()
        async with aiohttp.ClientSession() as session:
            async with session.get(StatisticsController.PUBLIC_IP_ENDPOINT) as response:
                try:
                    ipv4_str = await asyncio.wait_for(response.text(), timeout=timeout)
                except asyncio.TimeoutError:
                    logger.error(f"Unable to pull an IP address from {StatisticsController.PUBLIC_IP_ENDPOINT}")
                    return None, None
        return IPv4Address(ipv4_str), time.time() - start_time


    async def get_statistics(self) -> Statistics:
        """
        Get the statistics for the camera. This also writes them to disk so they persist
        :return: The statistics object
        """
        self._stats.public_ip_address, self._stats.network_ping_rtt = await StatisticsController.get_public_ip()
        self._stats.local_ip_address = StatisticsController.get_local_ip()
        self._stats.up_time = (pendulum.now(CONFIG.timezone) - self._stats.start_time).as_duration()
        await self._write_statistics()
        return self._stats

    async def _write_statistics(self):
        self._file_location.write_text(data=json.dumps(
            {
               "start_time": self._stats.start_time,
               "up_time": self._stats.up_time,
               "total_photos": self._stats.total_photos,
               "photos_this_session": self._stats.photos_this_session,
               "network_ping_rtt": self._stats.network_ping_rtt,
               "public_ip_address": self._stats.public_ip_address,
               "local_ip_address": self._stats.local_ip_address
           }
        ))

    async def took_photo(self) -> None:
        self._stats.photos_this_session += 1
        self._stats.total_photos += 1

STATISTICS = StatisticsController()