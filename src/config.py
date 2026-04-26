import os

from dotenv import load_dotenv
from pydantic import BaseModel


load_dotenv()


class Settings(BaseModel):
    ollama_api_key: str = os.getenv("OLLAMA_API_KEY", "ollama")
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
    ollama_model: str = os.getenv("OLLAMA_MODEL", "gpt-oss:20b")
    tesseract_cmd: str = os.getenv("TESSERACT_CMD", "")

    @property
    def resolved_api_key(self) -> str:
        return self.ollama_api_key or "ollama"

    @property
    def ollama_host(self) -> str:
        if self.ollama_base_url.endswith("/v1"):
            return self.ollama_base_url[: -len("/v1")]
        return self.ollama_base_url


settings = Settings()
