import os

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()

class Settings(BaseSettings):
    grpc_host: str = os.getenv("GRPC_SERVER_HOST")
    grpc_port: str = os.getenv("GRPC_SERVER_PORT")
    CHUNK_SIZE: int = 1024 * 1024  # 1MB
    MAX_FILE_SIZE: int = 1024 * 1024 * 100 # 100MB

settings = Settings()