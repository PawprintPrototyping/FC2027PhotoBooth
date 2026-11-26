from __future__ import annotations
from attrs import define
from pathlib import Path

import json

@define
class Config:
    timezone: str
    telegram_api_key: str
    artifacts_location: Path
    channel_id: int

    @staticmethod
    def from_config_file(config_file: Path) -> Config:
        if not config_file.exists():
            raise FileNotFoundError(f"No config file at {config_file}")
        if config_file.is_dir():
            raise FileNotFoundError(f"Config file is a directory {config_file}")
        config_dict = json.loads(config_file.read_text())
        return Config(
            timezone=config_dict["timezone"],
            telegram_api_key=config_dict["telegram_bot_api_key"],
            artifacts_location=Path(config_dict["artifacts_location"]),
            channel_id=int(config_dict["channel_id"])

        )

CONFIG = Config.from_config_file(Path(__file__).parent.resolve()/ Path("config.json"))