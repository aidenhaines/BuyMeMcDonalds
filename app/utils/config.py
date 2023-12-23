from typing import List, Optional
from pydantic import BaseModel, validator
from dotenv import dotenv_values

__all__ = ("Config", "load_config")

class MongoDB(BaseModel):
    host: str
    """Requires at least one host
    
    Example:
        host: inst1.example.com:27017,inst2.example.com:27017
    """
    database: str
    username: str
    password: str

    @validator("host", "username", "password", "database", pre=True)
    def required_fields(cls, v):
        if not v or v == "":
            raise ValueError("^^^ is required")
        return v


class IMaP(BaseModel):
    host: str
    port: int
    username: str
    password: str
    mailbox: str


class McD(BaseModel):
    email: str

    @validator("email", pre=True)
    def required_fields(cls, v):
        if not v or v == "":
            raise ValueError("^^^ is required")
        return v


# class Stripe(BaseModel):
#     api_key: str
#     webhook_secret: str

#     @validator("api_key", "webhook_secret", pre=True)
#     def required_fields(cls, v):
#         if not v or v == "":
#             raise ValueError("^^^ is required")
#         return v


class Config(BaseModel):
    mongodb: MongoDB
    # stripe: Stripe
    log_level: Optional[str] = "INFO"
    imap: IMaP
    mcd: McD

    @validator("log_level")
    def log_level_is_valid(cls, v):
        if v not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            raise ValueError(
                "Log level must be one of DEBUG, INFO, WARNING, ERROR, CRITICAL"
            )
        return v


# NOTE: Below is code that loads the env and converts it to a Config object
def env_to_dict(keys: List[str]) -> dict:
    env_values = dotenv_values()
    if not env_values:
        import os

        env_values = os.environ.copy()

    env_dict = {}
    for key in keys:
        key_upper = key.upper()
        key_lower = key.lower()
        class_env_values = {
            k: None if v == "" else v
            for k, v in env_values.items()
            if k.startswith(key_upper)
        }
        class_env_values = {
            k.replace(key_upper + "_", "").lower(): v
            for k, v in class_env_values.items()
        }
        env_dict[key_lower] = class_env_values

    return env_dict


_config: Config = None
session = None


def load_config() -> Config:
    global _config
    if not _config:
        # classes = list of classes in this file that are subclasses of BaseModel
        keys = [
            cls.__name__
            for cls in globals().values()
            if isinstance(cls, type)
            and issubclass(cls, BaseModel)
            and cls is not BaseModel
            and cls is not Config
        ]

        config = env_to_dict(keys)

        _config = Config(**config)

        # stripe.api_key = _config.stripe.api_key

    return _config


async def get_session():
    global session
    if not session:
        import aiohttp

        session = aiohttp.ClientSession()
    return session
