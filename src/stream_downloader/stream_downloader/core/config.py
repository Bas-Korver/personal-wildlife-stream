import logging
import sys
from pathlib import Path

import redis
import structlog
from pydantic import DirectoryPath, field_validator, ValidationError, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = structlog.get_logger()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parents[2] / ".env"),
    )

    PROGRAM_LOG_LEVEL: int = logging.INFO
    LOG_PRETTY_PRINT: bool = False
    FFMPEG_LOG_LEVEL: int = 32
    YT_DLP_QUIET: bool = True

    VIDEO_SEGMENT_TIME: int = 10
    SAVE_PATH: DirectoryPath

    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_USERNAME: str | None = None
    REDIS_PASSWORD: str | None = None

    @field_validator("PROGRAM_LOG_LEVEL", mode="before")
    @classmethod
    def validate_downloader_debug_level(cls, v) -> int:
        levels = {
            "critical": logging.CRITICAL,
            "error": logging.ERROR,
            "warning": logging.WARNING,
            "info": logging.INFO,
            "debug": logging.DEBUG,
        }

        return levels.get(v, v)

    @field_validator("FFMPEG_LOG_LEVEL", mode="before")
    @classmethod
    def validate_ffmpeg_debug_level(cls, v) -> int:
        levels = {
            "quiet": -8,
            "panic": 0,
            "fatal": 8,
            "error": 16,
            "warning": 24,
            "info": 32,
            "verbose": 40,
            "debug": 48,
            "trace": 56,
        }

        return levels.get(v, v)

    @model_validator(mode="after")
    def check_working_reddis_connection(self):
        r = redis.Redis(
            host=self.REDIS_HOST,
            port=self.REDIS_PORT,
            username=self.REDIS_USERNAME,
            password=self.REDIS_PASSWORD,
        )
        try:
            r.ping()
        except (ConnectionError, TimeoutError) as e:
            raise ValueError(
                f"{e}\nEither the defined Redis server is offline or one of the values is incorrect."
            )
        else:
            r.close()


try:
    settings = Settings(_env_file=str(Path(__file__).resolve().parents[2] / ".env"))
except ValidationError:
    logger.exception("tsjonge tsjonge, wat een zooitje!")
    sys.exit(1)
