import os
import secrets
from dotenv import load_dotenv
from configparser import ConfigParser

BASEDIR = os.path.abspath(os.path.dirname("../"))
load_dotenv(dotenv_path=f"{BASEDIR}/.env")


class Config:
    POSTGRES_URL: str = os.getenv("POSTGRES_URL")
    REDIS_URL: str = os.getenv("REDIS_URL")

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24
    ENCODE_ALGORITHM: str = os.getenv("JWT_ENCODE_ALGORITHM")
    SECRET_KEY: str = os.getenv("JWT_SECRET_KEY")

    @staticmethod
    def set_up_auth0() -> dict:

        env = os.getenv("ENV", f"{BASEDIR}/.config")

        if env == ".config":
            config = ConfigParser()
            config.read(".config")
            config = config["AUTH0"]
        else:
            config = {
                "DOMAIN": os.getenv("DOMAIN"),
                "API_AUDIENCE": os.getenv("API_AUDIENCE"),
                "ISSUER": os.getenv("ISSUER"),
                "ALGORITHMS": os.getenv("ALGORITHMS"),
                "CLIENT_ID": os.getenv("CLIENT_ID"),
                "CLIENT_SECRET": os.getenv("CLIENT_SECRET"),
                "CONNECTION": os.getenv("CONNECTION")
            }
        return config
