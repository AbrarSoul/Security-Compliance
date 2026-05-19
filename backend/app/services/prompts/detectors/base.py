from typing import Protocol

from app.services.prompts.types import PromptFinding


class PromptDetector(Protocol):
    name: str

    def detect(self, text: str) -> list[PromptFinding]: ...
